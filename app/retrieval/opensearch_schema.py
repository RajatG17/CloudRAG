INDEX_NAME = "knowledge-chunks-v2"

EMBEDDING_DIMENSIONS = 512

CHUNKER_VERSION = "char-900-overlap-150-v1"

def build_index_mapping() -> dict:
    
    return {
        "settings": {
            "index.knn": True,
        },
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "embedding": {
                    "type": "knn_vector",
                    "dimension": EMBEDDING_DIMENSIONS,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                    },
                },
                "text": {
                    "type": "text",
                },
                "chunk_id": {
                    "type": "keyword",
                },
                "document_id": {
                    "type": "keyword",
                },
                "tenant_id": {
                    "type": "keyword",
                },
                "source": {
                    "type": "keyword",
                },
                "source_key": {
                    "type": "keyword",
                },
                "page": {
                    "type": "integer",
                },
                "chunk_index": {
                    "type": "integer",
                },
                "chunker_version": {
                    "type": "keyword",
                },
                "embedding_model": {
                    "type": "keyword",
                },
                "content_sha256": {
                    "type": "keyword",
                },
                "s3_version_id": {
                    "type": "keyword",
                },
            },
        },
    }