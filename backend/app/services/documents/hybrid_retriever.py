import os
from typing import List, Dict, Any
from opensearchpy import OpenSearch, RequestsHttpConnection

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

    async def hybrid_search(self, query: str, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Execute a hybrid search combining Vector (k-NN) and BM25 (Full-text).
        """
        search_query = {
            "size": limit,
            "query": {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "content_text": {
                                    "query": query,
                                    "boost": 1.0
                                }
                            }
                        },
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_vector,
                                    "k": limit,
                                    "boost": 2.0
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        try:
            # Sync call for now, can be wrapped in run_in_executor if needed, 
            # but usually fine in this context if opensearch responds fast.
            response = self.client.search(index=self.index_name, body=search_query)
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            print(f"OpenSearch Search Error: {e}")
            return []

    async def index_chunk(self, chunk_id: str, content: str, embedding: List[float], metadata: Dict[str, Any]):
        """
        Index a scholarship chunk for hybrid search.
        """
        document = {
            "content_text": content,
            "embedding": embedding,
            "metadata": metadata
        }
        try:
            self.client.index(index=self.index_name, id=chunk_id, body=document, refresh=True)
        except Exception as e:
            print(f"OpenSearch Indexing Error: {e}")

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
                    "content_text": {"type": "text"},
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
