import argparse
import hashlib
import tempfile
from pathlib import Path, PurePosixPath

import boto3

from app.cloud.bedrock_client import (
    get_bedrock_runtime_client,
)
from app.cloud.config import get_aws_settings
from app.cloud.opensearch_client import (
    get_opensearch_client,
)
from app.cloud.s3_storage import (
    S3DocumentStorage,
)
from app.embeddings.bedrock import (
    BedrockEmbeddingProvider,
)
from app.ingestion.chunker import chunk_text
from app.ingestion.parser import extract_pages
from app.retrieval.opensearch_schema import CHUNKER_VERSION
from app.retrieval.opensearch_store import (
    OpenSearchVectorStore,
)


def sha256_text(value: str) -> str:

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()

def build_chunks(
        local_path: Path,
        bucket: str,
        key: str,
        tenant_id: str,
        metadata: dict,
) -> tuple[str, list[dict]]:

    version_id = (
        metadata["version_id"]
        or "unversioned"
    )

    document_id = sha256_text(
        f"{bucket}:{key}:{version_id}"
    )

    chunks = []

    for page_number, page_text in extract_pages(
        local_path
    ):

        page_chunks = chunk_text(
            page_text,
            chunk_size=900,
            overlap=150
        )

        for chunk_index, text in enumerate(page_chunks):

            chunk_id = sha256_text(
                f"{document_id}:{CHUNKER_VERSION}:{page_number}:{chunk_index}"
            )

            chunks.append({
                "chunk_id": chunk_id,
                "document_id": document_id,
                "tenant_id": tenant_id,
                "source": PurePosixPath(key).name,
                "source_key": key,
                "page": page_number,
                "chunk_index": chunk_index,
                "chunker_version": CHUNKER_VERSION,
                "embedding_model": (
                    "amazon.titan-embed-text-v2:0"
                ),
                "content_sha256": metadata["sha256"],
                "s3_version_id": version_id,
                "text": text,
            })

    if not chunks:
        raise ValueError(
            "Document contains no extractable text"
        )

    return document_id, chunks

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--key",
        required=True,
    )

    parser.add_argument(
        "--tenant",
        default="demo",
    )

    parser.add_argument(
        "--max-chunks",
        type=int,
        default=100,
    )

    args = parser.parse_args()

    if args.max_chunks < 1:
        raise ValueError(
            "max-chunks must be positive"
        )

    settings = get_aws_settings()

    session = boto3.Session(
        profile_name=settings.profile,
        region_name=settings.region,
    )

    storage = S3DocumentStorage(
        bucket=settings.bucket,
        session=session,
    )

    embedding_provider = BedrockEmbeddingProvider(
        client=get_bedrock_runtime_client(),
        dimensions=512,
    )

    vector_store = OpenSearchVectorStore(
        client=get_opensearch_client(),
        embedding_provider=embedding_provider,
    )

    metadata = storage.get_document_metadata(
        key=args.key,
        tenant_id=args.tenant,
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        local_path = (
            Path(temp_dir)
            / PurePosixPath(args.key).name
        )

        storage.download_document(
            key=args.key,
            destination=local_path,
            tenant_id=args.tenant,
        )

        document_id, chunks = build_chunks(
            local_path=local_path,
            bucket=settings.bucket,
            key=args.key,
            tenant_id= args.tenant,
            metadata=metadata,
        )

        print(f"Document ID: {document_id}")
        print(f"Chunks produced: {len(chunks)}")

        if len(chunks) > args.max_chunks:
            raise ValueError(
                f"Document has {len(chunks)} chunks."
                f"Limit is {args.max_limit}."
                "Increase the limit explicitly if the inference cost is acceptable."
            )

        total_tokens=0

        for number, chunk in enumerate(chunks, start=1):

            result = embedding_provider.embed_text(
                chunk["text"]
            )

            chunk["embedding"] = result.vector
            chunk["embedding_model"] = result.model_id

            total_tokens += result.input_tokens

            print(
                f"Embeded {number}/{len(chunks)} | tokens={result.input_tokens}"
            )

        indexed_count = vector_store.index_chunks(
            chunks
        )

        print("\nIndexing completed")

        print(f"Document ID: {document_id}")
        print(f"Chunks submitted: {indexed_count}")
        print(f"Embedding input tokens: {total_tokens}")

if __name__ == "__main__":
    main()




