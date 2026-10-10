import json

from pathlib import Path

from app.retrieval.chroma_store import get_collection

ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = ROOT / "data" / "processed"

def index_documents():
    
    collection = get_collection()
    
    for file_path in PROCESSED_DIR.glob("*.jsonl"):
        with file_path.open(
            "r",
            encoding = "utf-8",
        ) as file:
            chunks = [
                json.loads(line) 
                for line in file
                if line.strip()
            ]
            
        if not chunks:
            continue
        
        source = chunks[0]["source"]
        
        collection.delete(
            where={"source": source}
        )
        
        batch_size=100
        
        for offset in range(0, len(chunks), batch_size):
            batch = chunks[offset:offset+batch_size]
            
            documents = []
            ids = []
            embeddings = []
            metadatas = []
            
            for chunk in batch:
                
                ids.append(chunk["id"])
                
                documents.append(chunk["text"])
                
                embeddings.append(chunk["embedding"])
                
                metadatas.append(
                    {
                        "source": chunk["source"],
                        "page": chunk["page"],
                        "tenant_id": chunk["tenant_id"],
                        "content_sha256": chunk["content_sha256"],
                        "embedding_model": chunk["embedding_model"],
                    }
                )
            
            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )          
        
        print(
            f"Indexed {len(chunks)} chunks from {source}"
        )
        
if __name__ == "__main__":
    index_documents()
