from app.cloud.bedrock_client import (
    get_bedrock_runtime_client,
)

from app.embeddings.bedrock import (
    BedrockEmbeddingProvider,
)

from app.llm.bedrock import (
    BedrockGenerationProvider,
)

def main():
    
    client = get_bedrock_runtime_client()
    
    embeddings = BedrockEmbeddingProvider(
        client=client
    )
    
    generator = BedrockGenerationProvider(
        client=client
    )
    
    print("=" * 60)
    print("CLoudRAG Bedrock Smoke Test")
    print("="* 60)
    
    embedding_result = embeddings.embed_text(
        "Tha payment service uses exponential"
        "backoff with jitter for transient failures."
    )
    
    print(
        f"Model:{embedding_result.model_id}"
    )
    
    print(
        f"Dimensions: {embedding_result.dimensions}"
    )
    
    print(
        f"Input tokens: {embedding_result.input_tokens}"
    )

    print(
        f"Latency: {embedding_result.latency_ms} ms"
    )

    print(
        f"First 5 values: "
        f"{embedding_result.vector[:5]}"
    )

    assert embedding_result.dimensions == 512

    print("\n[2] Testing Nova Lite")

    generation_result = generator.generate(
        "Explain the purpose of idempotency keys "
        "in payment processing in two sentences."
    )

    print("\nAnswer:")
    print(generation_result.text)

    print("\nInference metrics:")

    print(
        f"Model: {generation_result.model_id}"
    )

    print(
        f"Input tokens: "
        f"{generation_result.input_tokens}"
    )

    print(
        f"Output tokens: "
        f"{generation_result.output_tokens}"
    )

    print(
        f"Server latency: "
        f"{generation_result.server_latency_ms} ms"
    )

    print(
        f"Client latency: "
        f"{generation_result.client_latency_ms} ms"
    )

    print(
        f"Stop reason: "
        f"{generation_result.stop_reason}"
    )

    assert generation_result.text

    assert (
        generation_result.stop_reason == "end_turn"
    ), "Generation did not finish normally"

    print("\nBEDROCK SMOKE TEST PASSED")


if __name__ == "__main__":
    main()