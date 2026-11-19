from app.cloud.opensearch_client import (
    get_opensearch_client,
)
from app.retrieval.opensearch_schema import (
    INDEX_NAME,
)

client = get_opensearch_client()

mapping = client.indices.get_mapping(
    index = INDEX_NAME
)

properties = mapping[
    INDEX_NAME
]["mappings"]["properties"]


print("Index:", INDEX_NAME)

print(
    "Tenant field type:",
    properties["tenant_id"]["type"],
    
)

assert properties["embedding"]["dimension"] == 512
assert properties["tenant_id"]["type"] == "keyword"

print("Index schema verification passed")
