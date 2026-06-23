"""
Tests for the Phoenix AI Evaluation module.
"""
import os
import math
import pytest
import tempfile
import torch

from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.agents.sandbox import PhoenixSandbox
from ai_project.evaluation.evaluator import PhoenixEvaluator


@pytest.fixture
def evaluator():
    """Sets up a minimal evaluator with a tiny model for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy training file and train a tiny tokenizer
        code_file = os.path.join(tmpdir, "code.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write("x = 1\ny = 2\nprint(x + y)\n")

        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)

        args = PhoenixModelArgs(
            vocab_size=100, n_layers=1, dim=16, n_heads=2,
            hidden_dim=32, max_seq_len=64
        )
        model = PhoenixTransformer(args)
        model.is_trained = True

        sandbox = PhoenixSandbox(sandbox_dir=tmpdir)
        eval_engine = PhoenixEvaluator(model, tokenizer, sandbox, device="cpu")

        yield eval_engine


def test_perplexity_returns_finite(evaluator):
    """Tests that perplexity calculation returns a finite number for a trained model."""
    ppl = evaluator.compute_perplexity("x = 1\ny = 2\n")
    assert isinstance(ppl, float)
    assert not math.isinf(ppl)
    assert ppl > 0


def test_perplexity_untrained_returns_inf():
    """Tests that an untrained model returns infinite perplexity."""
    with tempfile.TemporaryDirectory() as tmpdir:
        code_file = os.path.join(tmpdir, "code.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write("x = 1\n")

        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)
        args = PhoenixModelArgs(vocab_size=100, n_layers=1, dim=16, n_heads=2, hidden_dim=32, max_seq_len=64)
        model = PhoenixTransformer(args)
        model.is_trained = False

        eval_engine = PhoenixEvaluator(model, tokenizer, device="cpu")
        ppl = eval_engine.compute_perplexity("test text")
        assert math.isinf(ppl)


def test_code_execution_evaluation(evaluator):
    """Tests code execution evaluation returns correct structure."""
    samples = [
        "print('hello')",
        "x = 1 + 2\nprint(x)",
    ]
    results = evaluator.evaluate_code_execution(samples, timeout=5.0)

    assert results["total"] == 2
    assert "success" in results
    assert "failed" in results
    assert "success_rate" in results
    assert "details" in results
    assert len(results["details"]) == 2


def test_report_generation(evaluator):
    """Tests that generate_report returns a comprehensive report."""
    report = evaluator.generate_report(
        test_text="x = 1\ny = 2\n",
        code_samples=["print(1)"]
    )

    assert "timestamp" in report
    assert "model_trained" in report
    assert "model_params" in report
    assert "perplexity" in report
    assert "code_execution" in report
