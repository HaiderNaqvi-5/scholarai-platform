"""Route-ordering regression guard (broken-#4).

FastAPI/Starlette walk ``app.routes`` in registration order and dispatch to the
first route whose compiled path regex matches. A literal-segment route (e.g.
``/visa/start``) registered *after* a parameterized route that shares the same
prefix (e.g. ``/{session_id}``) is fragile: it only keeps working today because
the param is typed ``uuid.UUID`` and non-UUID literals 422 out rather than
being swallowed. This test asserts the ordering invariant directly (literal
paths registered before parameterized ones for the same prefix) so it stays
meaningful even if a param type is ever loosened to ``str``.
"""

from app.core.config import settings
from app.main import create_app


def _route_index_map() -> dict[str, int]:
    app = create_app()
    return {route.path: index for index, route in enumerate(app.routes) if hasattr(route, "path")}


def _assert_literal_before_param(index_map: dict[str, int], prefix: str) -> None:
    """For every route under ``prefix``, literal first-segments must be
    registered before any route whose corresponding segment is a param
    placeholder (``{...}``)."""
    literal_indices: list[tuple[str, int]] = []
    param_indices: list[tuple[str, int]] = []

    for path, index in index_map.items():
        if not path.startswith(prefix + "/"):
            continue
        remainder = path[len(prefix) + 1 :]
        first_segment = remainder.split("/", 1)[0]
        if first_segment.startswith("{"):
            param_indices.append((path, index))
        else:
            literal_indices.append((path, index))

    assert literal_indices, f"expected at least one literal route under {prefix}"
    assert param_indices, f"expected at least one parameterized route under {prefix}"

    max_literal = max(literal_indices, key=lambda item: item[1])
    min_param = min(param_indices, key=lambda item: item[1])

    assert max_literal[1] < min_param[1], (
        f"literal route {max_literal[0]!r} (index {max_literal[1]}) is registered "
        f"AFTER parameterized route {min_param[0]!r} (index {min_param[1]}) under "
        f"{prefix} -- literal paths must be registered first so they are not "
        f"shadowed by the param route."
    )


def test_interview_visa_literal_routes_registered_before_session_id_param():
    index_map = _route_index_map()
    prefix = f"{settings.API_V1_PREFIX}/interviews"

    assert f"{prefix}/visa/start" in index_map
    assert f"{prefix}/{{session_id}}" in index_map

    _assert_literal_before_param(index_map, prefix)


def test_curation_ingestion_run_bulk_retry_registered_before_run_id_param():
    index_map = _route_index_map()
    prefix = f"{settings.API_V1_PREFIX}/curation/ingestion-runs"

    assert f"{prefix}/bulk-retry" in index_map
    assert f"{prefix}/{{run_id}}" in index_map

    _assert_literal_before_param(index_map, prefix)
