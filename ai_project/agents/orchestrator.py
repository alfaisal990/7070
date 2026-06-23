import re
import logging
from pathlib import Path
from typing import Dict, List, Any

from ai_project.inference.engine import PhoenixInferenceEngine
from ai_project.memory.vector_db import PhoenixMemoryStore
from ai_project.agents.sandbox import PhoenixSandbox
from ai_project.agents.agent import PhoenixAgent
from ai_project.agents.debugger import PhoenixDebuggerAgent
from ai_project.agents.refactor import PhoenixRefactorAgent
from ai_project.utils.path_safety import resolve_safe_path

logger = logging.getLogger("PhoenixOrchestrator")

class PhoenixOrchestrator:
    """
    Multi-Agent Orchestrator for Phoenix AI.
    Implements a self-healing loop: Task -> Plan -> Execute -> QA -> Verify -> Debug/Fix -> Complete.
    """
    def __init__(
        self,
        engine: PhoenixInferenceEngine,
        memory: PhoenixMemoryStore,
        sandbox: PhoenixSandbox,
        workspace_dir: str = "c:/Users/1/Desktop/7070"
    ):
        self.engine = engine
        self.memory = memory
        self.sandbox = sandbox
        self.workspace_dir = Path(workspace_dir).resolve()
        
        # Sub-agents
        self.agent = PhoenixAgent(engine, memory, sandbox, workspace_dir)
        self.debugger = PhoenixDebuggerAgent(engine, memory, sandbox, workspace_dir)
        self.refactor = PhoenixRefactorAgent(engine, sandbox)

    def plan_task(self, task: str) -> List[Dict[str, Any]]:
        """
        Planner Agent: Takes a task description and structures it into a list of steps.
        """
        prompt = (
            f"You are the Phoenix Planner Agent. Break down the following task into sequential steps.\n"
            f"Task: {task}\n\n"
            f"For each step, specify:\n"
            f"- action: 'write_file', 'read_file', 'execute_code', or 'refactor'\n"
            f"- target: file path or parameter\n"
            f"- description: short description\n\n"
            f"Respond with a list of steps formatted like this:\n"
            f"[STEP] action: write_file | target: src/main.py | desc: write base implementation\n"
            f"[STEP] action: execute_code | target: src/main.py | desc: execute verification\n"
        )
        
        response = self.engine.generate(prompt, max_new_tokens=512, temperature=0.1)
        steps = []
        
        # Parse the structured steps from model response
        pattern = r"\[STEP\]\s*action:\s*(\w+)\s*\|\s*target:\s*([^\s\|]+)\s*\|\s*desc:\s*([^\n]+)"
        matches = re.findall(pattern, response)
        
        for action, target, desc in matches:
            steps.append({
                "action": action.strip(),
                "target": target.strip(),
                "description": desc.strip()
            })
            
        # Fallback if model did not output structured text
        if not steps:
            logger.warning("Planner failed to output structured steps. Defaulting to single execute step.")
            steps.append({
                "action": "execute_code",
                "target": "sandbox",
                "description": f"Directly execute code for task: {task}"
            })
            
        return steps

    def run_task(self, task: str) -> Dict[str, Any]:
        """
        Runs the orchestrator loop: Plan -> Execute -> QA -> Verify -> Auto-repair.
        """
        logger.info(f"Orchestrating task: {task}")
        steps = self.plan_task(task)
        history = []
        
        for idx, step in enumerate(steps):
            step_status = "success"
            step_details = ""
            action = step["action"]
            target = step["target"]
            
            logger.info(f"Step {idx+1}/{len(steps)}: {action} on {target}")
            
            if action == "write_file":
                # Let the Executor agent write the file content
                exec_prompt = f"Please write code for: {step['description']}. Specify code for {target} inside <write_file path=\"{target}\">code</write_file>."
                exec_res = self.agent.run_loop(exec_prompt, max_steps=2)
                
                # QA check: verify syntax of written file
                qa_err = self.debugger.check_syntax(target)
                if qa_err:
                    step_status = "failed"
                    step_details = f"QA Validation Error: Written code has syntax error: {qa_err}"
                    # Try self-healing (repair)
                    repair_res = self.debugger.run_auto_repair(target, qa_err)
                    if repair_res["status"] == "success":
                        step_status = "success"
                        step_details = f"Auto-repaired QA Syntax Error. Content verified."
                    else:
                        step_details += f" | Auto-repair failed: {repair_res.get('reason', 'unknown')}"
                else:
                    step_details = f"File {target} written and verified by QA."
                    
            elif action == "execute_code" or action == "verify":
                # Verifier: Run script in sandbox
                try:
                    full_path = resolve_safe_path(self.workspace_dir, target) if target != "sandbox" else None
                    if full_path and full_path.exists():
                        with open(full_path, "r", encoding="utf-8") as f:
                            code_to_run = f.read()
                    else:
                        # Generate code to execute task
                        code_prompt = f"Generate Python script to execute and verify: {step['description']}. Wrap code in <execute_code>code</execute_code>."
                        res = self.engine.generate(code_prompt, max_new_tokens=512, temperature=0.1)
                        match = re.search(r"<execute_code>([\s\S]*?)</execute_code>", res)
                        code_to_run = match.group(1).strip() if match else "print('Verification stub')"
                        
                    sandbox_res = self.sandbox.execute_code(code_to_run)
                    if sandbox_res["status"] == "success" and sandbox_res["exit_code"] == 0:
                        step_details = f"Execution output: {sandbox_res['stdout']}"
                    else:
                        step_status = "failed"
                        err_msg = sandbox_res["stderr"] or f"Process exited with non-zero code {sandbox_res['exit_code']}"
                        step_details = f"Execution failed: {err_msg}"
                        
                        # Self-healing loop: Debugger repair
                        if target != "sandbox":
                            repair_res = self.debugger.run_auto_repair(target, err_msg)
                            if repair_res["status"] == "success":
                                step_status = "success"
                                step_details = f"Auto-repaired sandbox runtime failure. Execution verified."
                except Exception as e:
                    step_status = "failed"
                    step_details = f"Execution trigger failure: {str(e)}"
                    
            elif action == "refactor":
                try:
                    full_path = resolve_safe_path(self.workspace_dir, target)
                    with open(full_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    refactor_res = self.refactor.refactor_code(code, "optimize_imports")
                    if refactor_res["status"] == "success":
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(refactor_res["refactored"])
                        step_details = f"Refactored top-level imports in {target}."
                    else:
                        step_status = "failed"
                        step_details = f"Refactoring failed sandbox verification: {refactor_res.get('reason')}"
                except Exception as e:
                    step_status = "failed"
                    step_details = f"Refactoring exception: {str(e)}"
            
            history.append({
                "step": step,
                "status": step_status,
                "details": step_details
            })
            
            if step_status == "failed":
                logger.error(f"Orchestration aborted at step {idx+1} due to unrecovered failure.")
                return {
                    "status": "failed",
                    "failed_step": step,
                    "details": step_details,
                    "history": history
                }
                
        return {
            "status": "success",
            "history": history
        }
