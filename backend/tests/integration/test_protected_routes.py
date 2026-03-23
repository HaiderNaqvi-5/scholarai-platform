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
    assert v1_response.headers.get("X-API-V1-Sunset-Days") == "90"

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


def test_api_v2_route_inventory_snapshot_from_openapi(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json().get("paths", {})

    expected_v2_prefixes = [
        "/api/v2/recommendations",
        "/api/v2/documents",
        "/api/v2/interviews",
        "/api/v2/profile",
        "/api/v2/scholarships",
        "/api/v2/analytics",
    ]
    for prefix in expected_v2_prefixes:
        assert any(path == prefix or path.startswith(f"{prefix}/") for path in paths)

    known_non_parity_surfaces = [
        "/api/v2/auth",
        "/api/v2/curation",
        "/api/v2/saved-opportunities",
        "/api/v2/mentor",
        "/api/v2/health",
    ]
    for prefix in known_non_parity_surfaces:
        assert not any(path == prefix or path.startswith(f"{prefix}/") for path in paths)
