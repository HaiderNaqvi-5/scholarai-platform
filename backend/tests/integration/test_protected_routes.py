def test_saved_opportunities_requires_authentication(client):
    response = client.get("/api/v1/saved-opportunities")

    assert response.status_code == 401
