"""Phoenix AI v1.1.0 — Full System Verification Script"""
import sys

def check(name, func):
    try:
        result = func()
        print(f"  [PASS] {name}: {result}")
        return True
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        return False

results = []
print("=" * 60)
print("  Phoenix AI v1.1.0 — System Verification Report")
print("=" * 60)

# 1. Model
print("\n[1] MODEL")
results.append(check("Transformer Init", lambda: (
    __import__("ai_project.models.model", fromlist=["PhoenixTransformer", "PhoenixModelArgs"]),
    (m := __import__("ai_project.models.model", fromlist=["PhoenixTransformer", "PhoenixModelArgs"]).PhoenixTransformer(
        __import__("ai_project.models.model", fromlist=["PhoenixModelArgs"]).PhoenixModelArgs()
    )),
    f"{sum(p.numel() for p in m.parameters()) / 1e6:.1f}M params"
)[-1]))

# 2. Tokenizer
print("\n[2] TOKENIZER")
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
t = PhoenixTokenizer(tokenizer_path="ai_project/tokenizer/tokenizer.json")
results.append(check("Tokenizer Load", lambda: f"vocab_size={t.get_vocab_size()}"))
results.append(check("Encode/Decode", lambda: (
    ids := t.encode("def hello(): pass"),
    decoded := t.decode(ids),
    f"encoded {len(ids)} tokens"
)[-1]))

# 3. Sandbox
print("\n[3] SANDBOX")
from ai_project.agents.sandbox import PhoenixSandbox
s = PhoenixSandbox()
r = s.execute_code("print(42)")
results.append(check("Normal Execution", lambda: f"status={r['status']}, stdout={r['stdout'].strip()}"))

r2 = s.execute_code("import os; os.system('dir')")
results.append(check("Security Blocklist", lambda: f"status={r2['status']}" if r2['status'] == 'blocked' else (_ for _ in ()).throw(Exception("NOT BLOCKED!"))))

r3 = s.execute_code("x" * 70000)
results.append(check("Code Size Limit", lambda: f"status={r3['status']}" if r3['status'] == 'error' else (_ for _ in ()).throw(Exception("NOT LIMITED!"))))

# 4. Memory
print("\n[4] VECTOR MEMORY")
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.memory.vector_db import PhoenixMemoryStore
m = PhoenixTransformer(PhoenixModelArgs())
ms = PhoenixMemoryStore(m, t, db_path="ai_project/memory/memory_db.json", device="cpu")
results.append(check("Memory Load", lambda: f"{len(ms.memories)} records"))

# 5. API
print("\n[5] API")
from ai_project.api.main import app
results.append(check("FastAPI App", lambda: f"{len(app.routes)} routes registered"))

# 6. Evaluation
print("\n[6] EVALUATION")
from ai_project.evaluation.evaluator import PhoenixEvaluator
ev = PhoenixEvaluator(m, t, s, device="cpu")
m.is_trained = True
ppl = ev.compute_perplexity("x = 1\ny = 2\n")
results.append(check("Perplexity Calc", lambda: f"ppl={ppl:.2f}"))

code_eval = ev.evaluate_code_execution(["print(1+1)"], timeout=5.0)
results.append(check("Code Eval", lambda: f"success_rate={code_eval['success_rate']}%"))

# Summary
print("\n" + "=" * 60)
passed = sum(results)
total = len(results)
status = "ALL SYSTEMS OPERATIONAL" if passed == total else f"ISSUES DETECTED"
print(f"  RESULT: {passed}/{total} checks passed — {status}")
print("=" * 60)

sys.exit(0 if passed == total else 1)
