from typing import Any

from opensearchpy import helpers

from app.retrieval.opensearch_schema import (
    EMBEDDING_DIMENSIONS,
    INDEX_NAME,
)


class OpenSearchVectorStore:
    
    def __init__(self,
                 client: Any,
                 embedding_provider: Any,
                 index_name: str = INDEX_NAME,
    ):
        
        self.client = client
        self.embedding_provider = embedding_provider
        self.index_name = index_name
        
    def index_chunks(
        self,
        chunks: list[dict],
    ) -> int:
        
        if not chunks:
            return 0
        
        actions = []
        
        for chunk in chunks:
            
            vector = chunk["embedding"]
            
            if len(vector) != EMBEDDING_DIMENSIONS:
                raise ValueError(
                    "Invalid embedding dimension"
                )
                
            document = dict(chunk)
            
            actions.append(
                {
                    "_op_type": "index",
                    "_index": self.index_name,
                    "_id": chunk["chunk_id"],
                    "_source": document,
                }  
            )
            
        success_count, _ = helpers.bulk(
            self.client,
            actions,
            chunk_size=20,
            raise_on_error=True,
            raise_on_exception=True,
            request_timeout=90,
        )
        
        return success_count
    
    def search(
        self,
        query: str,
        tenant_id: str,
        k: int= 5,
    ) -> list[dict]:
        
        if not query.strip():
            return []
        
        if not tenant_id:
            raise ValueError("tenant_id is required")
        
        if k<1 or k>20:
            raise ValueError(
                "K must be between 1 and 20"
            )
            
        embedding_result = (
            self.embedding_provider.embed_text(query)
        )
        
        
        vector = embedding_result.vector
        
        if len(vector) != EMBEDDING_DIMENSIONS:
            raise ValueError(
                "Query embedding dimension mismatch"
            )
            
        search_body = {
            "size": k,
            "_source": {
                "excludes": ["embedding"],
            },
            "query": {
                "knn": {
                    "embedding": {
                        "vector": vector,
                        "k": k, 
                        "filter": {
                            "term": {
                                "tenant_id": tenant_id,
                            }
                        },
                    }
                }
            }
        }
        
        response = self.client.search(
            index=self.index_name,
            body=search_body,
        )
        
        results = []
        
        for hit in response["hits"]["hits"]:
            
            source = hit["_source"]
            
            # Defense-in-depth verification
            
            if source["tenant_id"] != tenant_id:
                raise RuntimeError(
                    "Unexpected cross-tenant result"
                )
            
            results.append(
                {
                    "text": source["text"],
                    "source": source["source"],
                    "page": source["page"],
                    "source_key": source["source_key"],
                    "document_id": source["document_id"],
                    "se_version_id": source["s3_version_id"],
                    "score": hit["_score"],
                }
            )
            
        return results
                