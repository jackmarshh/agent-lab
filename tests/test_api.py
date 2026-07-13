from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_diagnose_returns_evidence_and_safe_action(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_MODE", "demo")
    response = client.post("/diagnose", json={"service": "checkout-api", "incident": "503 rate is rising"})
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "needs_attention"
    assert len(body["evidence"]) == 9
    assert "checkout-api is the top consumer" in body["recommended_action"]
    assert any("connection pool exhausted" in item["detail"] for item in body["evidence"])
    assert "ran read-only log inspection" in body["trace"]
    assert "ran upstream dependency check" in body["trace"]
