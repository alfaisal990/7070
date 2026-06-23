import os
import json
import pytest
from fastapi.testclient import TestClient
from ai_project.api.main import app, AI_DATA_PATH
from ai_project.api.auth import create_access_token, Roles

def test_ai_explorer_api():
    # Load original data if exists to restore later
    original_data = None
    if os.path.exists(AI_DATA_PATH):
        with open(AI_DATA_PATH, "r", encoding="utf-8") as f:
            original_data = json.load(f)
            
    # Write a clean mock test dataset
    mock_dataset = {
      "categories": [
        {
          "id": "gen_ai",
          "name": "الذكاء الاصطناعي التوليدي",
          "description": "توليد محتوى جديد",
          "models": [
            {
              "name": "TestGPT",
              "developer": "TestOpen",
              "type": "LLM",
              "parameters": "10B",
              "use_case": "توليد نصوص تجريبية"
            }
          ]
        },
        {
          "id": "nlp",
          "name": "معالجة اللغات",
          "description": "فهم اللغات",
          "models": []
        }
      ]
    }
    
    with open(AI_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(mock_dataset, f)
        
    try:
        with TestClient(app) as client:
            # 1. Search without query
            resp_all = client.get("/api/ai_explorer/search")
            assert resp_all.status_code == 200
            cats = resp_all.json()["categories"]
            assert len(cats) == 2
            assert cats[0]["id"] == "gen_ai"
            assert len(cats[0]["models"]) == 1
            assert cats[0]["models"][0]["name"] == "TestGPT"
            
            # 2. Search with query matching TestGPT
            resp_q = client.get("/api/ai_explorer/search?query=test")
            assert resp_q.status_code == 200
            assert len(resp_q.json()["categories"][0]["models"]) == 1
            
            # 3. Search with query NOT matching
            resp_none = client.get("/api/ai_explorer/search?query=nonexistent")
            assert resp_none.status_code == 200
            assert len(resp_none.json()["categories"][0]["models"]) == 0
            
            # 4. Search by category_id
            resp_cat = client.get("/api/ai_explorer/search?category_id=nlp")
            assert resp_cat.status_code == 200
            assert len(resp_cat.json()["categories"]) == 1
            assert resp_cat.json()["categories"][0]["id"] == "nlp"
            
            # 5. Add model to invalid category_id
            op_token = create_access_token("op1", "operator", Roles.OPERATOR)
            op_headers = {"Authorization": f"Bearer {op_token}"}
            resp_add_fail = client.post("/api/ai_explorer/add", json={
                "category_id": "invalid_cat",
                "name": "NewModel",
                "developer": "NewDev",
                "type": "NewType",
                "parameters": "1B",
                "use_case": "Test cases"
            }, headers=op_headers)
            assert resp_add_fail.status_code == 404
            
            # 6. Add model successfully to nlp category
            resp_add_ok = client.post("/api/ai_explorer/add", json={
                "category_id": "nlp",
                "name": "TestBERT",
                "developer": "TestGoogle",
                "type": "Encoder",
                "parameters": "100M",
                "use_case": "تصنيف النصوص البرمجية"
            }, headers=op_headers)
            assert resp_add_ok.status_code == 200
            assert resp_add_ok.json()["status"] == "success"
            
            # 7. Search again and check if TestBERT exists under nlp
            resp_verify = client.get("/api/ai_explorer/search?category_id=nlp")
            assert resp_verify.status_code == 200
            nlp_models = resp_verify.json()["categories"][0]["models"]
            assert len(nlp_models) == 1
            assert nlp_models[0]["name"] == "TestBERT"
            
    finally:
        # Restore original database
        if original_data is not None:
            with open(AI_DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(original_data, f, ensure_ascii=False, indent=2)
        elif os.path.exists(AI_DATA_PATH):
            os.remove(AI_DATA_PATH)
