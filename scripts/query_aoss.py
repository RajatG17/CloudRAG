import argparse

from app.cloud.bedrock_client import (
    get_bedrock_runtime_client,
)
from app.cloud.opensearch_client import (
    get_opensearch_client,
)
from app.embeddings.bedrock import (
    BedrockEmbeddingProvider,
)
from app.retrieval.opensearch_store import (
    OpenSearchVectorStore,
)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "question",
        type=str,
    )

    parser.add_argument(
        "--tenant",
        default="demo",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
    )

    args = parser.parse_args()

    embedding_provider = BedrockEmbeddingProvider(
        client=get_bedrock_runtime_client(),
        dimensions=512,
    )

    store = OpenSearchVectorStore(
        client=get_opensearch_client(),
        embedding_provider=embedding_provider,
    )

    results = store.search(
        query=args.question,
        tenant_id=args.tenant,
        k=args.top_k,
    )

    print(f"\nRetrieved {len(results)} chunks\n")

    for index, result in enumerate(
        results,
        start=1,
    ):

        print(f"[{index}] {result['source']}")

        print(f"Page: {result['page']}")
        print(f"Score: {result['score']}")

        print(result["text"])
        print("-" * 60)


if __name__ == "__main__":
    main()