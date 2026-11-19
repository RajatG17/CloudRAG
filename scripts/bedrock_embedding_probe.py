from app.cloud.bedrock_client import (
    get_bedrock_runtime_client,
)

from app.embeddings.bedrock import (
    BedrockEmbeddingProvider,
)

def dot_product(a,b):
    return sum(
        x*y
        for x, y in zip(a, b)
    )
    
def main():
    
    provider = BedrockEmbeddingProvider(
        client=get_bedrock_runtime_client()
    )
    
    documents = [
        (
            "payments",
            "Payment requests use idempotency keys to prevent duplicate transactions."
            
        ),
        (
            "cooking",
            "Banana bread is baked in an oven using flour and mashed potatoes."
        ),
        (
            "networking",
            "A NAT Gateway allows instances in "
            "private subnets to initiate outbound "
            "connections."
        ),
    ]
    
    query = (
        "How do we avoid charging customers twice?"
    )
    
    query_vector = provider.embed_text(
        query
    ).vector
    
    scores = []
    
    for document_id, text in documents:
        
        document_vector = provider.embed_text(
            text
        ).vector
        
        score = dot_product(
            query_vector,
            document_vector,
        )
        
        scores.append(
            (document_id, score)
        )
        
    scores.sort(
        key=lambda item: item[1],
        reverse = True,
    )
    
    print("\nSemantic retrieval ranking")
    
    for document_id, score in scores:
        print(
            f"{document_id}: {score:.4f}"
        )
        
if __name__ == "__main__":
    main()