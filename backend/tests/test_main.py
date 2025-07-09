import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "InsightBot API" in response.json()["message"]

def test_health():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_query_endpoint():
    """Test query endpoint with sample query"""
    response = client.post(
        "/api/query",
        json={"query": "What is machine learning?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "answer" in data
    assert "sources" in data

def test_upload_endpoint():
    """Test upload endpoint"""
    test_file = ("test.txt", "This is a test document", "text/plain")
    response = client.post(
        "/api/upload",
        files={"file": test_file}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"

def test_workflow_status():
    """Test workflow status endpoint"""
    response = client.get("/api/workflow/status")
    assert response.status_code == 200
    data = response.json()
    assert data["workflow_initialized"] == True
    assert "agents" in data