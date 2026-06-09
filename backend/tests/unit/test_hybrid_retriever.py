"""
Unit tests for OpenSearchHybridRetriever — P2-19 remediation.

Tests cover:
1. fail-closed construction: no OPENSEARCH_HOST → RuntimeError (no admin/admin default).
2. fail-closed construction: HOST set but USER or PASS missing → RuntimeError.
3. build_if_configured() returns None when OPENSEARCH_HOST unset (no-op, no client).
4. Index mapping uses space_type='cosinesimil', NOT 'l2'.
5. _is_configured() gate reflects env correctly.
"""
import importlib
import sys
import types
import pytest


# ---------------------------------------------------------------------------
# Helpers: stub out the opensearchpy import so the module loads without the
# optional opensearchpy package (which may not be installed in the test env).
# ---------------------------------------------------------------------------

def _patch_opensearchpy(monkeypatch):
    """Insert a minimal opensearchpy stub into sys.modules if absent."""
    if "opensearchpy" in sys.modules:
        return  # real package present — use it

    fake_os = types.ModuleType("opensearchpy")

    class _FakeClient:
        def __init__(self, **kwargs):
            self._init_kwargs = kwargs

        def search(self, **kw):
            return {"hits": {"hits": []}}

        def index(self, **kw):
            pass

        def delete(self, **kw):
            pass

        class indices:  # noqa: N801
            @staticmethod
            def exists(**kw):
                return False

            @staticmethod
            def create(*a, **kw):
                pass

    fake_os.OpenSearch = _FakeClient
    fake_os.RequestsHttpConnection = object

    monkeypatch.setitem(sys.modules, "opensearchpy", fake_os)


def _load_module(monkeypatch):
    """(Re)load hybrid_retriever with the current sys.modules state."""
    _patch_opensearchpy(monkeypatch)
    # Force reimport so env changes take effect
    mod_name = "app.services.recommendations.hybrid_retriever"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    return importlib.import_module(mod_name)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestIsConfiguredGate:
    def test_unset_host_returns_false(self, monkeypatch):
        monkeypatch.delenv("OPENSEARCH_HOST", raising=False)
        mod = _load_module(monkeypatch)
        assert mod._is_configured() is False

    def test_set_host_returns_true(self, monkeypatch):
        monkeypatch.setenv("OPENSEARCH_HOST", "localhost")
        mod = _load_module(monkeypatch)
        assert mod._is_configured() is True


class TestConstructionFailClosed:
    def test_no_host_raises_runtime_error(self, monkeypatch):
        """With OPENSEARCH_HOST unset, constructor must raise — not silently use admin/admin."""
        monkeypatch.delenv("OPENSEARCH_HOST", raising=False)
        monkeypatch.delenv("OPENSEARCH_USER", raising=False)
        monkeypatch.delenv("OPENSEARCH_PASS", raising=False)
        mod = _load_module(monkeypatch)
        with pytest.raises(RuntimeError, match="OPENSEARCH_HOST is not set"):
            mod.OpenSearchHybridRetriever()

    def test_host_set_but_no_user_raises(self, monkeypatch):
        monkeypatch.setenv("OPENSEARCH_HOST", "localhost")
        monkeypatch.delenv("OPENSEARCH_USER", raising=False)
        monkeypatch.setenv("OPENSEARCH_PASS", "somepass")
        mod = _load_module(monkeypatch)
        with pytest.raises(RuntimeError, match="OPENSEARCH_USER and OPENSEARCH_PASS"):
            mod.OpenSearchHybridRetriever()

    def test_host_set_but_no_pass_raises(self, monkeypatch):
        monkeypatch.setenv("OPENSEARCH_HOST", "localhost")
        monkeypatch.setenv("OPENSEARCH_USER", "someuser")
        monkeypatch.delenv("OPENSEARCH_PASS", raising=False)
        mod = _load_module(monkeypatch)
        with pytest.raises(RuntimeError, match="OPENSEARCH_USER and OPENSEARCH_PASS"):
            mod.OpenSearchHybridRetriever()

    def test_all_set_constructs_without_error(self, monkeypatch):
        monkeypatch.setenv("OPENSEARCH_HOST", "localhost")
        monkeypatch.setenv("OPENSEARCH_USER", "myuser")
        monkeypatch.setenv("OPENSEARCH_PASS", "mypassword")
        mod = _load_module(monkeypatch)
        retriever = mod.OpenSearchHybridRetriever()
        assert retriever is not None


class TestBuildIfConfigured:
    def test_returns_none_when_host_unset(self, monkeypatch):
        """build_if_configured() must be a no-op (None) when OPENSEARCH_HOST is absent."""
        monkeypatch.delenv("OPENSEARCH_HOST", raising=False)
        monkeypatch.delenv("OPENSEARCH_USER", raising=False)
        monkeypatch.delenv("OPENSEARCH_PASS", raising=False)
        mod = _load_module(monkeypatch)
        result = mod.OpenSearchHybridRetriever.build_if_configured()
        assert result is None

    def test_returns_instance_when_fully_configured(self, monkeypatch):
        monkeypatch.setenv("OPENSEARCH_HOST", "localhost")
        monkeypatch.setenv("OPENSEARCH_USER", "myuser")
        monkeypatch.setenv("OPENSEARCH_PASS", "mysecret")
        mod = _load_module(monkeypatch)
        result = mod.OpenSearchHybridRetriever.build_if_configured()
        assert result is not None
        assert isinstance(result, mod.OpenSearchHybridRetriever)


class TestIndexMappingCosine:
    """The knn_vector field must use cosinesimil, not l2."""

    def _get_mapping_settings(self, mod):
        """Extract the mapping dict from create_index_if_not_exists source."""
        import inspect
        src = inspect.getsource(mod.OpenSearchHybridRetriever.create_index_if_not_exists)
        return src

    def test_space_type_is_cosinesimil(self, monkeypatch):
        monkeypatch.setenv("OPENSEARCH_HOST", "localhost")
        monkeypatch.setenv("OPENSEARCH_USER", "u")
        monkeypatch.setenv("OPENSEARCH_PASS", "p")
        mod = _load_module(monkeypatch)
        src = self._get_mapping_settings(mod)
        assert "cosinesimil" in src, (
            "Index mapping must use space_type='cosinesimil' to match the pgvector cosine path"
        )
        assert "\"l2\"" not in src and "'l2'" not in src, (
            "space_type must NOT be 'l2' — it is incompatible with the pgvector cosine rankings"
        )

    def test_mapping_dict_space_type_at_runtime(self, monkeypatch):
        """Drive create_index_if_not_exists against a fake client and inspect the body passed."""
        captured = {}

        class _CapturingIndices:
            @staticmethod
            def exists(index):
                return False

            @staticmethod
            def create(index_name, body):
                captured["body"] = body

        class _CapturingClient:
            def __init__(self, **kwargs):
                self.indices = _CapturingIndices()

        import types as _types
        fake_os = _types.ModuleType("opensearchpy")
        fake_os.OpenSearch = _CapturingClient
        fake_os.RequestsHttpConnection = object
        monkeypatch.setitem(sys.modules, "opensearchpy", fake_os)

        monkeypatch.setenv("OPENSEARCH_HOST", "localhost")
        monkeypatch.setenv("OPENSEARCH_USER", "u")
        monkeypatch.setenv("OPENSEARCH_PASS", "p")

        mod_name = "app.services.recommendations.hybrid_retriever"
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        mod = importlib.import_module(mod_name)

        import asyncio
        retriever = mod.OpenSearchHybridRetriever()
        asyncio.run(retriever.create_index_if_not_exists())

        assert "body" in captured, "create() was not called on the fake client"
        embedding_mapping = (
            captured["body"]["mappings"]["properties"]["embedding"]["method"]
        )
        assert embedding_mapping["space_type"] == "cosinesimil", (
            f"Expected cosinesimil, got {embedding_mapping['space_type']!r}"
        )
