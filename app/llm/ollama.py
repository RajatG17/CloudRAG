import os

import requests

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate",
)

MODEL_NAME = os.getenv(
    "OLLAMA_MODEL",
    "qwen3.5:4b"
)

def generate_response(prompt: str) -> str:
    
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3
            }
        },
        timeout=120,
    )
    
    response.raise_for_status()
    
    payload = response.json()
    
    return payload["response"].strip()

