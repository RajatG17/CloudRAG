# import io
# import json

# import pytest

# from app.embeddings.bedrock import (
#     BedrockEmbeddingProvider,
# )

# from app.llm.bedrock import (
#     BedrockGenerationProvider,
# )

# class FakeBedrockClient:
    
#     def __init__(self):
#         self.last_embedding_request = None
#         self.last_generation_reqest = None
        
#     def invoke_model(self, **kwargs):
        
#         self.last_embedding_request = kwargs
        
#         payload = json.loads(
#             kwargs["body"]
#         )
        
#         dimensions = payload["dimensions"]
        
#         embedding = (
#             [1.0] + [0.0] * (dimensions-1)
#         )
        
#         response = {
#             "embedding": embedding,
#             "inputTextTokenCount": 12,
#         }
        
#         return {
#             "body": io.BytesIO(
#                 json.dumps(response).encode()
#             ),
#             "ResponseMetadata": {
#                 "RequestId": "test-embedding-id"
#             },
#         }
        
#     def converse(self, **kwargs):
        
#         self.last_generation_request = kwargs
        
#         return {
#             "output": {
#             "message": {
#                 "role": "assistant",
#                 "content": [
#                     {
#                         "text": (
#                             "The service uses "
#                             "exponential backoff [1]."
#                         )
#                     }
#                 ],
#             }
#         },
#         "stopReason": "end_turn",
#         "usage": {
#             "inputTokens": 100,
#             "outputTokens": 25,
#             "totalTokens": 125,
#         },
#         "metrics": {
#             "latencyMs": 850
#         },
#         "ResponseMetadata": {
#             "RequestId": "test-generation-id"
#         },
#     }


# def test_embedding_dimensions():
    
#     provider = BedrockEmbeddingProvider(
#         client=FakeBedrockClient(),
#         dimensions=512,
#     )
    
#     result = provider.embed_text(
#         "Test document",
#     )
    
#     assert result.dimensions == 512
#     assert len(result.vector) == 512
    
#     assert result.input_tokens == 12
    
# def test_embedding_payload():
    
#     client = FakeBedrockClient()
    
#     provider=BedrockEmbeddingProvider(
#         client=client,
#         dimensions=512,
#     )
    
#     provider.embed_text(
#         "How do payment retries work?"
#     )
    
#     payload = json.loads(
#         client.last_embedding_request["body"]
#     )
    
#     assert payload["dimensions"] == 512
#     assert payload["normalize"] is True
    
#     assert payload["inputText"] == (
#         "How do payment retries work?"
#     )
    
# def test_empty_embedding_input():
    
#     provider = BedrockEmbeddingProvider(
#         client=FakeBedrockClient()
#     )
    
#     with pytest.raises(ValueError):
#         provider.embed_text("")

# def test_invalid_embedding_dimensions():
#     with pytest.raises(ValueError):
        
#         BedrockEmbeddingProvider(
#             client=FakeBedrockClient(),
#             dimensions=384,
#         )

# def test_generation():
    
#     provider = BedrockGenerationProvider(
#         client=FakeBedrockClient(),
#     )
    
#     result = provider.generate(
#         "Explain retry policies"
#     )
    
#     assert "exponential backoff" in result.text
    
#     assert result.input_tokens == 100
#     assert result.output_tokens == 25
    
#     assert result.stop_reason == "end_turn"
    
# def test_generation_request():
    
#     client = FakeBedrockClient()
    
#     provider = BedrockGenerationProvider(
#         client=client,
#         max_tokens=256,
#     )
    
#     provider.generate(
#         "Explain idempotency"
#     )
    
#     request = client.last_generation_reqest
    
#     assert request["inferenceConfig"]["maxtokens"] == 256
#     assert request["inferenceConfig"]["temperature"] == 0.0
    
# def test_empty_generation_prompt():
    
#     provider = BedrockGenerationProvider(
#         client=FakeBedrockClient(),
#     )
    
#     with pytest.raises(ValueError):
#         provider.generate("")
        

import io
import json

import pytest

from app.embeddings.bedrock import (
    BedrockEmbeddingProvider,
)

from app.llm.bedrock import (
    BedrockGenerationProvider,
)


class FakeBedrockClient:

    def __init__(self):
        self.last_embedding_request = None
        self.last_generation_request = None

    def invoke_model(self, **kwargs):

        self.last_embedding_request = kwargs

        payload = json.loads(
            kwargs["body"]
        )

        dimensions = payload["dimensions"]

        embedding = (
            [1.0] + [0.0] * (dimensions - 1)
        )

        response = {
            "embedding": embedding,
            "inputTextTokenCount": 12,
        }

        return {
            "body": io.BytesIO(
                json.dumps(response).encode()
            ),
            "ResponseMetadata": {
                "RequestId": "test-embedding-id"
            },
        }

    def converse(self, **kwargs):

        self.last_generation_request = kwargs

        return {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "text": (
                                "The service uses "
                                "exponential backoff [1]."
                            )
                        }
                    ],
                }
            },
            "stopReason": "end_turn",
            "usage": {
                "inputTokens": 100,
                "outputTokens": 25,
                "totalTokens": 125,
            },
            "metrics": {
                "latencyMs": 850
            },
            "ResponseMetadata": {
                "RequestId": "test-generation-id"
            },
        }


def test_embedding_dimensions():

    provider = BedrockEmbeddingProvider(
        client=FakeBedrockClient(),
        dimensions=512,
    )

    result = provider.embed_text(
        "Test document"
    )

    assert result.dimensions == 512
    assert len(result.vector) == 512
    assert result.input_tokens == 12


def test_embedding_payload():

    client = FakeBedrockClient()

    provider = BedrockEmbeddingProvider(
        client=client,
        dimensions=512,
    )

    provider.embed_text(
        "How do payment retries work?"
    )

    payload = json.loads(
        client.last_embedding_request["body"]
    )

    assert payload["dimensions"] == 512
    assert payload["normalize"] is True

    assert payload["inputText"] == (
        "How do payment retries work?"
    )


def test_empty_embedding_input():

    provider = BedrockEmbeddingProvider(
        client=FakeBedrockClient()
    )

    with pytest.raises(ValueError):
        provider.embed_text("")


def test_invalid_embedding_dimension():

    with pytest.raises(ValueError):

        BedrockEmbeddingProvider(
            client=FakeBedrockClient(),
            dimensions=384,
        )


def test_generation():

    provider = BedrockGenerationProvider(
        client=FakeBedrockClient()
    )

    result = provider.generate(
        "Explain retry policies."
    )

    assert "exponential backoff" in result.text

    assert result.input_tokens == 100
    assert result.output_tokens == 25

    assert result.stop_reason == "end_turn"


def test_generation_request():

    client = FakeBedrockClient()

    provider = BedrockGenerationProvider(
        client=client,
        max_tokens=256,
    )

    provider.generate(
        "Explain idempotency."
    )

    request = client.last_generation_request

    assert request["inferenceConfig"]["maxTokens"] == 256

    assert request["inferenceConfig"]["temperature"] == 0.0


def test_empty_generation_prompt():

    provider = BedrockGenerationProvider(
        client=FakeBedrockClient()
    )

    with pytest.raises(ValueError):
        provider.generate("")