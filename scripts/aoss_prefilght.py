from app.cloud.opensearch_client import (
    get_opensearch_client,
)

def main():
    
    client = get_opensearch_client()
    
    response = client.cat.indices(
        format="json"
    )
    
    print("OpenSearch connection successful")
    print("Existing indexes:", response)
    
if __name__ == "__main__":
    main()
    
    