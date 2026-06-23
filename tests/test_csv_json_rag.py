import os
import pytest
import tempfile
import csv
import json
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.memory.vector_db import PhoenixMemoryStore
from ai_project.memory.rag import PhoenixRAGPipeline

def test_rag_csv_and_json_ingestion():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy source for tokenizer training
        dummy_code = "print('hello')\n"
        code_file = os.path.join(tmpdir, "code.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(dummy_code)
        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)

        # Model args and model
        args = PhoenixModelArgs(
            vocab_size=100,
            n_layers=1,
            dim=16,
            n_heads=1,
            hidden_dim=32,
            max_seq_len=32
        )
        model = PhoenixTransformer(args)
        model.eval()

        db_path = os.path.join(tmpdir, "memory.json")
        store = PhoenixMemoryStore(model, tokenizer, db_path=db_path, device="cpu")
        pipeline = PhoenixRAGPipeline(store)

        # 1. Create and ingest CSV file
        csv_path = os.path.join(tmpdir, "test.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "role", "city"])
            writer.writerow(["Alice", "Engineer", "New York"])
            writer.writerow(["Bob", "Designer", "Paris"])

        res_csv = pipeline.ingest_file(csv_path, chunk_size=500, chunk_overlap=0)
        assert res_csv["status"] == "success"
        assert res_csv["file_name"] == "test.csv"

        # Check CSV memories in store
        csv_memories = [m for m in store.memories if m["metadata"]["source"] == "test.csv"]
        assert len(csv_memories) > 0
        all_csv_text = "\n".join([m["text"] for m in csv_memories])
        assert "Row 1: name is Alice, role is Engineer, city is New York" in all_csv_text
        assert "Row 2: name is Bob, role is Designer, city is Paris" in all_csv_text

        # 2. Create and ingest JSON file
        json_path = os.path.join(tmpdir, "test.json")
        json_data = {
            "app": "Phoenix",
            "settings": {
                "active": True,
                "version": 6.0
            },
            "tags": ["AI", "Autopilot"]
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f)

        res_json = pipeline.ingest_file(json_path, chunk_size=500, chunk_overlap=0)
        assert res_json["status"] == "success"
        assert res_json["file_name"] == "test.json"

        # Check JSON memories in store
        json_memories = [m for m in store.memories if m["metadata"]["source"] == "test.json"]
        assert len(json_memories) > 0
        all_json_text = "\n".join([m["text"] for m in json_memories])
        assert "app is Phoenix" in all_json_text
        assert "settings.active is True" in all_json_text
        assert "settings.version is 6.0" in all_json_text
        assert "tags[0] is AI" in all_json_text
        assert "tags[1] is Autopilot" in all_json_text
