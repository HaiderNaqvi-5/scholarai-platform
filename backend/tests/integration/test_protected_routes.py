def test_saved_opportunities_requires_authentication(client):
    response = client.get("/api/v1/saved-opportunities")

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["status"] == 401
    assert "request_id" in body["error"]
