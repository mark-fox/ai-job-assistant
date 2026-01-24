from fastapi.testclient import TestClient


def test_status_ok(client: TestClient):
    response = client.get("/status")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in {"ok", "degraded"}
    assert "version" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "environment" in data
    assert "llm_provider" in data
