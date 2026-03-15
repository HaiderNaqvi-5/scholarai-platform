from fastapi.testclient import TestClient


def test_health_endpoint_returns_200(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "0.1.0"
    assert payload["status"] in {"healthy", "degraded"}
