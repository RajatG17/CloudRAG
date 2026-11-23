import os
from functools import lru_cache

from app.retrieval.opensearch_store import (
    OpenSearchVectorStore,
)

from app.retrieval.chroma_store import (
    get_context as get_local_context,
)

from app.cloud.bedrock_client import (
    get_bedrock_runtime_client,
)

from app.cloud.opensearch_client import (
    get_opensearch_client,
)

from app.embeddings.bedrock import (
    BedrockEmbeddingProvider,
)

@lru_cache(maxsize=1)
def get_cloud_store():

    embedder = BedrockEmbeddingProvider(
        client=get_bedrock_runtime_client(),
        dimensions=512,
    )

    return OpenSearchVectorStore(
        client=get_opensearch_client(),
        embedding_provider=embedder,
    )


def get_context(
    query: str,
    k: int = 5,
    tenant_id: str = "demo",
) -> list[dict]:

    backend = os.getenv(
        "CLOUDRAG_RETRIEVER",
        "chroma",
    ).lower()

    if backend == "chroma":

        return get_local_context(
            query=query,
            k=k,
            tenant_id=tenant_id,
        )

    if backend == "opensearch":

        return get_cloud_store().search(
            query=query,
            tenant_id=tenant_id,
            k=k,
        )

    raise ValueError(
        f"Unknown retrieval backend: {backend}"
    )