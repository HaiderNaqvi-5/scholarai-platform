def test_saved_opportunities_requires_authentication(client):
    response = client.get("/api/v1/saved-opportunities")

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["status"] == 401
    assert "request_id" in body["error"]


def test_v1_deprecation_headers_and_v2_route_available(client):
    v1_response = client.post(
        "/api/v1/recommendations/evaluate",
        json={
            "predicted_ids": ["a", "b", "c"],
            "judged_relevance": {"a": 3, "b": 1, "c": 0},
            "k_values": [1, 3],
        },
    )
    assert v1_response.status_code == 401
    assert v1_response.headers.get("Deprecation") == "true"
    assert v1_response.headers.get("Sunset")
    assert "/api/v2" in (v1_response.headers.get("Link") or "")
    assert v1_response.headers.get("X-API-Contract-Version") == "v1"
    assert v1_response.headers.get("X-API-V1-Deprecation-Window") == "90"

    v2_response = client.post(
        "/api/v2/recommendations/evaluate",
        json={
            "predicted_ids": ["a", "b", "c"],
            "judged_relevance": {"a": 3, "b": 1, "c": 0},
            "k_values": [1, 3],
        },
    )
    assert v2_response.status_code == 401
    assert v2_response.headers.get("X-API-Contract-Version") == "v2"
    assert v2_response.headers.get("Deprecation") is None
