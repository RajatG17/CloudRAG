import json
import math
import os
import time
from dataclasses import dataclass
from typing import Any

DEFAULT_MODEL = "amazon.titan-embed-text-v2:0"

@dataclass(frozen=True)
class EmbeddingResult:
    vector: list[float]
    model_id: str
    dimensions: int
    input_tokens: int
    latency_ms: float
    request_id: str | None
    
class BedrockEmbeddingProvider:
    
    def __init__(self,
                 client: Any,
                 model_id: str | None = None,
                 dimensions: int | None = None,):
        
        self.client = client
        
        self.model_id = model_id or os.getenv(
            "BEDROCK_EMBED_MODEL",
            DEFAULT_MODEL
        )
        
        self.dimensions = (
            dimensions 
            if dimensions is not None
            else int(
                os.getenv(
                    "BEDROCK_EMBED_DIMENSIONS",
                    "512",
                )
            )
        )
        
        if self.dimensions not in (256, 512, 1024):
            raise ValueError(
                "Titan V2 supports 256, 512, or 1024 dimensions"
            )
            
    def embed_text(
        self,
        text: str,
    ) -> EmbeddingResult:
        
        if not isinstance(text, str) or not text.strip():
            raise ValueError(
                "Embedding input must be non-empty text"
            )
            
        if len(text) > 50_000:
            raise ValueError("Embedding input exceeds 50,000 characters")
        
        payload = {
            "inputText": text,
            "dimensions": self.dimensions,
            "normalize": True,
            "embeddingTypes": ["float"],
        }    
        
        start = time.perf_counter()
        
        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload),
        )
        
        latency_ms = (
            time.perf_counter() - start
        ) * 1000
        
        body = json.loads(
            response["body"].read()
        )
        
        vector = body["embedding"]
        
        if len(vector) != self.dimensions:
            raise RuntimeError(
                "Unexpected embedding dimension:"
                f"{len(vector)}"
            )
            
        if not all(
            isinstance(value, (int, float))
            and math.isfinite(value)
            for value in vector
        ):
            raise RuntimeError(
                "Embedding contains invalid numerical values"
            )
            
        return EmbeddingResult(
            vector=vector,
            model_id=self.model_id,
            dimensions=len(vector),
            input_tokens=body.get(
                "inputTextTokenCount",
                0
            ),
            latency_ms=round(latency_ms, 2),
            request_id=response.get(
                "ResponseMetadata", {}
            ).get("RequestId"),
        )
        
    def embed_texts(
        self, 
        texts: list[str],
    ) -> list[EmbeddingResult]:
        
        return [
            self.embed_text(text)
            for text in texts
        ]
        
    
    