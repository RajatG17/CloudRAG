import logging
import time
import uuid

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request, 
)

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
)

from opensearchpy.exceptions import (
    OpenSearchException,
)

from app.api.auth import (
    AuthContext,
    require_user
)

from app.api.schemas import (
    QueryMetadata,
    QueryRequest,
    QueryResponse,
    SourceReference,
)

logger = logging.getLogger("cloudrag.api")
logger.setLevel(logging.INFO)

app = FastAPI(
    title="CloudRAG API",
    version="0.2.5",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

def get_graph():
    from app.graph.workflow import graph
    return graph

def get_request_id(request: Request) -> str:

    event = request.scope.get("aws.event", {})

    request_id = (
        event.get("requestContext", {})
        .get("requestId")
    )

    return request_id or uuid.uuid4().hex

@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "cloudrag-query-api",
    }

@app.post(
    "/v1/query",
    response_model=QueryResponse,
)
def query(
    payload: QueryRequest,
    request: Request,
    user: AuthContext = Depends(require_user),
    graph= Depends(get_graph),
):
    request_id = get_request_id(request)

    started = time.perf_counter()

    try: 
        result = graph.invoke(
            {
                "question": payload.question,
                "tenant_id": user.tenant_id,
                "top_k": payload.top_k,
            }
        )

    except (
        ClientError,
        BotoCoreError,
        OpenSearchException,
    ):
        logger.exception(
            "RAG dependency failure request_ids=%s", request_id
        )

        raise HTTPException(
            status_code=503,
            detail="AI service temporarily inavailable",
        )

    except Exception:
        logger.exception(
            "Unexpected RAG error request_id=%s",
            request_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Internal query processing error",
        )

    contexts = result.get("contexts", [])

    sources = [
        SourceReference(
            citation=f"[{index}]",
            source=context["source"],
            page=context["page"],
            document_id=context.get("document_id"),
        )
        for index, context in enumerate(
            contexts, start=1,
        )
    ]

    metrics = result.get(
        "generation_metrics",
        {},
    )

    elapsed_ms = (
        time.perf_counter() - started
    ) * 1000

    logger.info(
        "query_complete request_id=%s "
        "tenant=%s retrieval_count=%d "
        "latency_ms=%.2f",
        request_id,
        user.tenant_id,
        len(contexts),
        elapsed_ms,
    )

    return QueryResponse(
        answer=result["answer"],
        sources=sources,
        metadata=QueryMetadata(
            request_id=request_id,
            retrieval_count=len(contexts),
            latency_ms=round(elapsed_ms, 2),
            model=metrics.get("model_id"),
        ),
    )

