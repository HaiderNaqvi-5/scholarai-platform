import os
import logging
from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch, RequestsHttpConnection
from app.models import Scholarship

logger = logging.getLogger(__name__)


def _is_configured() -> bool:
    """Return True only when OPENSEARCH_HOST is explicitly set in the environment."""
    return bool(os.getenv("OPENSEARCH_HOST"))


class OpenSearchHybridRetriever:
    """Hybrid BM25 + k-NN retriever backed by OpenSearch.

    Construction is gated on ``OPENSEARCH_HOST`` being set.  If the env var is
    absent, ``OpenSearchHybridRetriever()`` raises ``RuntimeError`` so callers
    that construct unconditionally (e.g. ``CurationService.__init__``) will see
    a clear error rather than silently connecting with default admin credentials.

    Callers that want an optional retriever should use
    ``OpenSearchHybridRetriever.build_if_configured()`` which returns ``None``
    when OpenSearch is not configured.
    """

    def __init__(self):
        host = os.getenv("OPENSEARCH_HOST")
        if not host:
            raise RuntimeError(
                "OPENSEARCH_HOST is not set — OpenSearchHybridRetriever cannot be constructed. "
                "Set OPENSEARCH_HOST (and OPENSEARCH_USER / OPENSEARCH_PASS) to enable hybrid search."
            )
        self.host = host
        self.port = int(os.getenv("OPENSEARCH_PORT", 9200))
        user = os.getenv("OPENSEARCH_USER")
        password = os.getenv("OPENSEARCH_PASS")
        if not user or not password:
            raise RuntimeError(
                "OPENSEARCH_USER and OPENSEARCH_PASS must both be set — "
                "no default credentials are allowed."
            )

        use_ssl = os.getenv("OPENSEARCH_USE_SSL", "false").lower() in ("1", "true", "yes")
        verify_certs = os.getenv("OPENSEARCH_VERIFY_CERTS", "false").lower() in ("1", "true", "yes")

        self.client = OpenSearch(
            hosts=[{'host': self.host, 'port': self.port}],
            http_auth=(user, password),
            use_ssl=use_ssl,
            verify_certs=verify_certs,
            connection_class=RequestsHttpConnection
        )
        self.index_name = "scholarships"

    @classmethod
    def build_if_configured(cls) -> "Optional[OpenSearchHybridRetriever]":
        """Return a retriever instance if OPENSEARCH_HOST is set, else None."""
        if not _is_configured():
            return None
        try:
            return cls()
        except Exception:
            logger.warning(
                "OpenSearch retriever unavailable; hybrid search disabled.",
                exc_info=True,
            )
            return None

    async def hybrid_search(self, query: str, query_vector: List[float], limit: int = 20) -> List[Dict[str, Any]]:
        """
        Execute a hybrid search combining Vector (k-NN) and BM25 (Full-text).
        """
        search_query = {
            "size": limit,
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^5", "provider_name^3", "summary^2", "field_tags^2", "funding_summary"],
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                                "boost": 1.5
                            }
                        },
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_vector,
                                    "k": limit * 2,
                                    "boost": 2.5
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            }
        }
        
        try:
            response = self.client.search(index=self.index_name, body=search_query)
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception:
            logger.warning("OpenSearch search error", exc_info=True)
            return []

    async def index_scholarship(self, scholarship: Scholarship, embedding: List[float]):
        """
        Index a scholarship record for hybrid search.
        """
        document = {
            "scholarship_id": str(scholarship.id),
            "title": scholarship.title,
            "provider_name": scholarship.provider_name,
            "summary": scholarship.summary,
            "funding_summary": scholarship.funding_summary,
            "country_code": scholarship.country_code,
            "field_tags": scholarship.field_tags,
            "degree_levels": scholarship.degree_levels,
            "embedding": embedding,
            "metadata": {
                "source_url": scholarship.source_url,
                "deadline_at": scholarship.deadline_at.isoformat() if scholarship.deadline_at else None
            }
        }
        try:
            self.client.index(index=self.index_name, id=str(scholarship.id), body=document, refresh=True)
        except Exception:
            logger.warning("OpenSearch indexing error", exc_info=True)

    async def delete_scholarship(self, scholarship_id: str):
        """
        Remove a scholarship from the index.
        """
        try:
            if self.client.indices.exists(index=self.index_name):
                self.client.delete(index=self.index_name, id=scholarship_id, ignore=[404])
        except Exception:
            logger.warning("OpenSearch deletion error", exc_info=True)

    async def create_index_if_not_exists(self):
        """
        Create the scholarship index with k-NN and text mappings.
        """
        settings = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                }
            },
            "mappings": {
                "properties": {
                    "scholarship_id": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "english"},
                    "provider_name": {"type": "text", "analyzer": "english"},
                    "summary": {"type": "text", "analyzer": "english"},
                    "funding_summary": {"type": "text", "analyzer": "english"},
                    "country_code": {"type": "keyword"},
                    "field_tags": {"type": "keyword"},
                    "degree_levels": {"type": "keyword"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 768, # Matches all-mpnet-base-v2
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {"ef_construction": 128, "m": 24}
                        }
                    },
                    "metadata": {"type": "object"}
                }
            }
        }
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(self.index_name, body=settings)
