"""Pins broken-#3: /api/v2 is a documented alias of v1 that must NOT
inherit v1's Deprecation/Sunset headers.

`app/api/v2/__init__.py` re-mounts the same v1 route handlers under the
`/api/v2` prefix (see the module docstring/comment there for why). The one
behavioral guarantee that alias relies on is that main.py's deprecation
middleware gates strictly on `API_V1_PREFIX`, so a v2 caller never sees
itself flagged as deprecated. This test drives one route that is mounted
identically under both prefixes and asserts v1 carries the deprecation
signal while v2 does not.
"""


_EVALUATE_PAYLOAD = {
    "predicted_ids": ["a", "b", "c"],
    "judged_relevance": {"a": 3, "b": 1, "c": 0},
    "k_values": [1, 3],
}


def test_v1_carries_deprecation_headers(client):
    # Auth-gated route: 401s before touching the DB, so no live Postgres
    # is needed just to observe the headers the middleware attaches.
    response = client.post("/api/v1/recommendations/evaluate", json=_EVALUATE_PAYLOAD)

    assert response.status_code == 401
    assert response.headers.get("Deprecation") == "true"
    assert response.headers.get("Sunset")
    assert response.headers.get("X-API-Contract-Version") == "v1"
    assert "/api/v2" in (response.headers.get("Link") or "")


def test_v2_alias_does_not_inherit_v1_deprecation_headers(client):
    response = client.post("/api/v2/recommendations/evaluate", json=_EVALUATE_PAYLOAD)

    assert response.status_code == 401
    assert response.headers.get("X-API-Contract-Version") == "v2"
    assert response.headers.get("Deprecation") is None
    assert response.headers.get("Sunset") is None
    assert response.headers.get("X-API-V1-Sunset-Days") is None
