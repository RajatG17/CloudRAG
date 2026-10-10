import hashlib

import json

from pathlib import Path

from app.ingestion.parser import extract_pages
from app.ingestion.chunker import chunk_text
from app.embeddings.local import embed_texts, MODEL_NAME

ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = ROOT / "data" / "raw"

PROCESSED_DIR = ROOT / "data" / "processed" 

def calculate_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()
    
    with file_path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
            
    return digest.hexdigest()
    
def process_document(file_path: Path, chunk_size: int = 900, overlap: int = 150) -> None:
    """Process a document by extracting text, chunking it, and generating embeddings.

    Args:
        file_path (Path): The path to the document file.
        chunk_size (int, optional): The maximum size of each chunk. Defaults to 900.
        overlap (int, optional): The number of overlapping characters between chunks. Defaults to 150.
    """
    
    print(f"Processing document: {file_path.name}")
    
    source = file_path.relative_to(RAW_DIR).as_posix()
    
    document_hash = calculate_sha256(file_path)
    
    pages = extract_pages(file_path)
    
    chunks = []
    
    for page_number, page_text in pages:
        
        page_chunks = chunk_text(page_text)
        
        for chunk_index, text in enumerate(page_chunks):
            identifier = (
                f"{source}:"
                f"{document_hash}:"
                f"{page_number}:"
                f"{chunk_index}"
            )
            
            chunk_id = hashlib.sha256(
                identifier.encode("utf-8")
            ).hexdigest()
            
            chunks.append({
                "id": chunk_id,
                "source": source,
                "page": page_number,
                "chunk_index": chunk_index,
                "tenant_id": "demo",
                "text": text,
            })
            
    if not chunks:
        raise ValueError(f"No chunks were generated for the document: {file_path.name}")
    
    texts = [chunk["text"] for chunk in chunks] 
    
    embeddings = embed_texts(texts)
    
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding
        
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    
    source_hash = hashlib.sha256(
        source.encode("utf-8")
    ).hexdigest()[:16]
    
    output_path = PROCESSED_DIR / f"{source_hash}.jsonl"
    
    with output_path.open("w", encoding="utf-8") as output:
        for chunk in chunks:
            output.write(
                json.dumps(chunk) + "\n"
            )
            
    print(f"Created {len(chunks)} chunks for {file_path.name}")
    
    return len(chunks)


def run_pipeline():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    total_chunks = 0 
    processed_files = 0
    
    for file_path in RAW_DIR.rglob("*"):
        if not file_path.is_file():
            continue
        
        if file_path.suffix.lower() not in {".pdf", ".txt"}:
            continue
        
        count = process_document(file_path)
        
        total_chunks += count
        
        processed_files += 1
        
    print("\bIngestion completed.")
    print(f"Documents processed: {processed_files}")
    print(f"Total chunks created: {total_chunks}")
    
if __name__ == "__main__":
    run_pipeline()
    
    
    
    