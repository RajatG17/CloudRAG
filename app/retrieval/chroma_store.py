from pathlib import Path

import chromadb

from app.embeddings.local import embed_texts

ROOT = Path(__file__).resolve().parents[2]

CHROMA_DIR = ROOT / "data" / "chroma"

def get_collection():
    
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    collection = client.get_or_create_collection(
        name="knowledge_chinks", 
        metadata={
            "hnsw:space": "cosine", 
        },
    )
    
    return collection

def get_context(
    query: str,
    k: int=5,
    tenant_id: str = "demo",
) ->list[dict]:
    
    if not query.strip():
        return []
    
    collection = get_collection()
    
    query_vector = embed_texts([query])[0]
    
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        where={
            "tenant_id": tenant_id,
        },
        include=[
            "documents",
            "metadatas",
            "distances"
        ],
    )
    
    contexts = []
    
    documents = results["documents"][0] 
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    
    if not documents:
        return []
    
    for document, metadata, distance in zip(
        documents, metadatas, distances
    ):
        contexts.append({
            "text": document,
            "source": metadata["source"],
            "page": metadata["page"],
            "distance": distance,
        })
        
    return contexts
    
    
    
    
    
    