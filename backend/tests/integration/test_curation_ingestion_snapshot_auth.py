def test_curation_ingestion_snapshot_get_requires_authentication(client):
    response = client.get(
        "/api/v1/curation/ingestion-runs/00000000-0000-0000-0000-000000000000/snapshot",
    )

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["status"] == 401
    assert "request_id" in body["error"]


def test_curation_ingestion_snapshot_clear_requires_authentication(client):
    response = client.delete(
        "/api/v1/curation/ingestion-runs/00000000-0000-0000-0000-000000000000/snapshot",
    )

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["status"] == 401
    assert "request_id" in body["error"]
