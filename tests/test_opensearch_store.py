from types import SimpleNamespace

import pytest

from app.retrieval.opensearch_schema import (
    build_index_mapping,
)
from app.retrieval.opensearch_store import (
    OpenSearchVectorStore,
)


class FakeEmbeddingProvider:

    def embed_text(self, text):

        return SimpleNamespace(
            vector=[0.0] * 512
        )


class FakeOpenSearchClient:

    def __init__(self):
        self.last_search = None

    def search(self, index, body):

        self.last_search = body

        return {
            "hits": {
                "hits": [
                    {
                        "_score": 0.92,
                        "_source": {
                            "tenant_id": "demo",
                            "text": "Payment retry strategy",
                            "source": "payments.txt",
                            "source_key": (
                                "uploads/demo/payments.txt"
                            ),
                            "page": 1,
                            "document_id": "doc-1",
                            "s3_version_id": "version-1",
                        },
                    }
                ]
            }
        }


def make_store(client=None):

    client = client or FakeOpenSearchClient()

    return OpenSearchVectorStore(
        client=client,
        embedding_provider=FakeEmbeddingProvider(),
    )


def test_index_dimension():

    mapping = build_index_mapping()

    properties = mapping["mappings"]["properties"]

    assert properties["embedding"]["dimension"] == 512
    assert properties["tenant_id"]["type"] == "keyword"


def test_search_returns_context():

    store = make_store()

    results = store.search(
        query="How do retries work?",
        tenant_id="demo",
        k=5,
    )

    assert len(results) == 1
    assert results[0]["source"] == "payments.txt"
    assert results[0]["page"] == 1


def test_search_applies_tenant_filter():

    client = FakeOpenSearchClient()

    store = make_store(client)

    store.search(
        query="Payment retries",
        tenant_id="demo",
        k=5,
    )

    filter_clause = client.last_search[
        "query"
    ]["knn"]["embedding"]["filter"]

    assert filter_clause == {
        "term": {
            "tenant_id": "demo"
        }
    }


def test_search_excludes_embedding():

    client = FakeOpenSearchClient()

    store = make_store(client)

    store.search(
        "Payment retries",
        tenant_id="demo",
    )

    assert "embedding" in client.last_search[
        "_source"
    ]["excludes"]


def test_empty_query():

    store = make_store()

    assert store.search(
        "",
        tenant_id="demo",
    ) == []


def test_invalid_k():

    store = make_store()

    with pytest.raises(ValueError):
        store.search(
            "Payment retries",
            tenant_id="demo",
            k=0,
        )


def test_dimension_mismatch():

    class InvalidEmbeddingProvider:

        def embed_text(self, text):

            return SimpleNamespace(
                vector=[0.0] * 384
            )

    store = OpenSearchVectorStore(
        client=FakeOpenSearchClient(),
        embedding_provider=InvalidEmbeddingProvider(),
    )

    with pytest.raises(ValueError):
        store.search(
            "Payment retries",
            tenant_id="demo",
        )