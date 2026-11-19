from app.cloud.opensearch_client import (
    get_opensearch_client,
)
from app.retrieval.opensearch_schema import (
    INDEX_NAME,
    build_index_mapping,
)


def main():
    
    client = get_opensearch_client()
    
    if client.indices.exists(index=INDEX_NAME):
        
        print(
            f"Index already exists: {INDEX_NAME}"
        )
        
        return

    response = client.indices.create(
        index=INDEX_NAME,
        body=build_index_mapping(),
    )
    
    print("Index creation response:")
    print(response)
    
if __name__ == "__main__":
    main()
    