from fastapi.testclient import TestClient

from app.api.auth import (
    AuthContext,
    require_user,
)

from app.api.main import (
    app,
    get_graph,
)

class FakeGraph:

    def invoke(self, state):

        assert state["tenant_id"] == "demo"

        return {
            "answer": (
                "The sercvice uses exponential backoff with jitter [1]."
            ),
            "contexts": [
                {
                    "text": "Retry Policy",
                    "source": "payments.txt",
                    "page": 2,
                    "document_id": "doc-123",
                }
            ],
            "generation_metrics": {
                "model_id":"test_model",
            },
        }

def fake_user():
    return AuthContext(
        subject="test_user",
        tenant_id="demo",
    )

def test_health():

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_query_requires_authentication():

    app.dependency_overrides.clear()

    with TestClient(app) as client:

        response = client.post(
            "/v1/query",
            json={
                "question": "How are failures handeled?"
            },
        )

    assert response.status_code == 401

def test_query_success():

    app.dependency_overrides[require_user] = fake_user
    app.dependency_overrides[get_graph] = FakeGraph

    try:
        with TestClient(app) as client:
            response = client.post(
                "/v1/query",
                json={
                    "question": "How are failures handled",
                    "top_k": 5,
                },
            )

        assert response.status_code == 200

        body = response.json()

        assert "exponential backoff" in body["answer"]

        assert body["sources"][0]["page"] == 2
        assert body["metadata"]["retrieval_count"] == 1

    finally:
        app.dependency_overrides.clear()

def test_invalid_top_k():

    app.dependency_overrides[require_user] = fake_user

    try:
        with TestClient(app) as client:
            response = client.post(
                "/v1/query",
                json={
                    "question": "Explain retries",
                    "top_k": 100,
                },
            )

        assert response.status_code == 422

    finally:
        app.dependency_overrides.clear()

