import re

def normalize_text(text: str) -> str:
    """Normalize text by removing extra whitespace and newlines.

    Args:
        text (str): The input text to normalize.
        
    """
    
    return re.sub(r"\s+", " ", text).strip()

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    """Chunk text into smaller pieces with specified size and overlap.

    Args:
        text (str): The input text to chunk.
        chunk_size (int, optional): The maximum size of each chunk. Defaults to 900.
        overlap (int, optional): The number of overlapping characters between chunks. Defaults to 150.

    Returns:
        list[str]: A list of text chunks.
    """
    
    if chunk_size <= 0:
        raise ValueError("chunk_size muse be positive")
    
    if overlap < 0 or overlap >= chunk_size: 
        raise ValueError("overlap must be non-negative and less than chunk_size")
    
    text = normalize_text(text)
    
    if not text:
        return []
    
    chunks = []
    
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        
        # Prefer word boundaries for chunking
        if end < len(text):
            boundary = text.rfind(
                " ",
                start + chunk_size // 2, 
                end
            )
            
            if boundary != -1:
                end = boundary
                
        chunk = text[start:end].strip()
        
        if chunk:
            chunks.append(chunk)
            
        if end == len(text):
            break
        
        start = max(start + 1, end - overlap)
        
    return chunks

