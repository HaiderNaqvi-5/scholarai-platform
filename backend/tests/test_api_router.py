from app.api.v1 import router


def test_phase_one_routes_are_registered():
    route_paths = {route.path for route in router.routes}

    assert "/auth/register" in route_paths
    assert "/profile" in route_paths
    assert "/scholarships" in route_paths
    assert "/applications" in route_paths
    assert "/admin/stats" in route_paths


def test_deferred_legacy_routes_are_not_registered():
    route_paths = {route.path for route in router.routes}

    assert "/credentials" not in route_paths
    assert "/mentorship/mentors" not in route_paths
