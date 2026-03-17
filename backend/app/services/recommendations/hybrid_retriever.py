import os
from typing import List, Dict, Any
from opensearchpy import OpenSearch, RequestsHttpConnection
from app.models import Scholarship

class OpenSearchHybridRetriever:
    def __init__(self):
        self.host = os.getenv("OPENSEARCH_HOST", "opensearch")
        self.port = int(os.getenv("OPENSEARCH_PORT", 9200))
        self.user = os.getenv("OPENSEARCH_USER", "admin")
        self.password = os.getenv("OPENSEARCH_PASS", "admin")
        
        self.client = OpenSearch(
            hosts=[{'host': self.host, 'port': self.port}],
            http_auth=(self.user, self.password),
            use_ssl=False,
            verify_certs=False,
            connection_class=RequestsHttpConnection
        )
        self.index_name = "scholarships"

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
        except Exception as e:
            print(f"OpenSearch Search Error: {e}")
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
        except Exception as e:
            print(f"OpenSearch Indexing Error: {e}")

    async def delete_scholarship(self, scholarship_id: str):
        """
        Remove a scholarship from the index.
        """
        try:
            if self.client.indices.exists(index=self.index_name):
                self.client.delete(index=self.index_name, id=scholarship_id, ignore=[404])
        except Exception as e:
            print(f"OpenSearch Deletion Error: {e}")

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
                            "space_type": "l2",
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
