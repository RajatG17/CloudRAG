import os
from dataclasses import asdict

from app.cloud.bedrock_client import (
    get_bedrock_runtime_client,
)
from app.llm.bedrock import (
    BedrockGenerationProvider,
)
from app.llm.ollama import (
    generate_response,
)


def generate_with_provider(
    prompt: str,
) -> dict:
    
    provider = os.getenv(
        "CLOUDRAG_LLM_PROVIDER",
        "ollama",
    ).lower()
    
    print(f"Using provider {provider}")
    
    if provider == "ollama":
        
        answer = generate_response(prompt)
        
        return {
            "text": answer,
            "metadata": {
                "provider": "ollama",
            },
        }
        
    if provider == "bedrock":
         
        generator = BedrockGenerationProvider(
            client=get_bedrock_runtime_client(),
        )
        
        result = generator.generate(prompt)
        
        if result.stop_reason != "end_turn":
            raise RuntimeError(
                "Bedrock generation ended without "
                "a confirmed complete response: "
                f"{result.stop_reason}"
            )
            
        metadata = asdict(result)
        metadata.pop("text")
        
        return {
            "text": result.text,
            "metadata": {
                "provider": "bedrock",
                **metadata,
            },
        }
        
    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )
    
    