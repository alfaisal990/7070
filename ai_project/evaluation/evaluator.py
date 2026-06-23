"""
Phoenix AI Evaluation Module.
Provides automated model quality assessment including perplexity
calculation and code execution success rate metrics.
"""

import time
import math
import torch
from typing import Dict, Any, Optional


class PhoenixEvaluator:
    """
    Automated model evaluation engine.
    Computes perplexity on test data and measures code execution success rates.
    """

    def __init__(self, model, tokenizer, sandbox=None, device: str = "cpu"):
        self.model = model
        self.tokenizer = tokenizer
        self.sandbox = sandbox
        self.device = device

    @torch.no_grad()
    def compute_perplexity(self, text: str, max_seq_len: int = 512) -> float:
        """
        Computes perplexity of the model on a given text sample.
        Lower perplexity = better language modeling capability.
        """
        if not getattr(self.model, "is_trained", True):
            return float("inf")

        tokens = self.tokenizer.encode(text)
        if len(tokens) < 2:
            return float("inf")

        # Truncate to max_seq_len
        tokens = tokens[:max_seq_len]

        input_ids = torch.tensor([tokens[:-1]], dtype=torch.long, device=self.device)
        target_ids = torch.tensor([tokens[1:]], dtype=torch.long, device=self.device)

        self.model.eval()
        logits, loss = self.model(input_ids, target_ids)

        if loss is None:
            return float("inf")

        perplexity = math.exp(loss.item())
        return perplexity

    def evaluate_code_execution(self, code_samples: list[str], timeout: float = 5.0) -> Dict[str, Any]:
        """
        Evaluates code execution success rate across a set of code samples.
        """
        if self.sandbox is None:
            return {"error": "Sandbox not available for code evaluation."}

        results = {
            "total": len(code_samples),
            "success": 0,
            "failed": 0,
            "timeout": 0,
            "details": []
        }

        for code in code_samples:
            res = self.sandbox.execute_code(code, timeout=timeout)
            status = res.get("status", "error")

            if status == "success" and res.get("exit_code", -1) == 0:
                results["success"] += 1
            elif status == "timeout":
                results["timeout"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "code_preview": code[:100] + "..." if len(code) > 100 else code,
                "status": status,
                "exit_code": res.get("exit_code", -1)
            })

        results["success_rate"] = (
            results["success"] / results["total"] * 100
            if results["total"] > 0 else 0.0
        )

        return results

    def generate_report(self, test_text: Optional[str] = None, code_samples: Optional[list[str]] = None) -> Dict[str, Any]:
        """
        Generates a comprehensive evaluation report.
        """
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_trained": getattr(self.model, "is_trained", False),
            "model_params": sum(p.numel() for p in self.model.parameters()),
            "device": self.device,
        }

        if test_text:
            report["perplexity"] = self.compute_perplexity(test_text)

        if code_samples:
            report["code_execution"] = self.evaluate_code_execution(code_samples)

        return report
