from app.cloud.opensearch_client import (
    get_opensearch_client,
)
from app.retrieval.opensearch_schema import (
    INDEX_NAME,
)

client = get_opensearch_client()

response = client.count(
    index=INDEX_NAME,
    body={
        "query": {
            "term": {
                "tenant_id": "demo"
            }
        }
    },
)

print(
    "Indexed demo tenant chunks:",
    response["count"],
)