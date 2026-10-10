from app.ingestion.chunker import (
    chunk_text,
    normalize_text
)

def test_normalize_text():
    
    text = "Hello world\n\ntest"
    
    assert normalize_text(text) == "Hello world test"
    
    
def test_empty_document():
    
    assert chunk_text("") == []
    

def test_short_document():
    
    text = "This is a short document."
    
    chunks = chunk_text(
        text=text,
        chunk_size=900,
        overlap=150,
    )
    
    assert len(chunks) == 1
    
    assert chunks[0] == text
    
def test_long_document():
    
    text = "Distributed systems require stability." * 100
    
    chunks = chunk_text(
        text,
        chunk_size=900,
        overlap=150
    )
    
    assert len(chunks) > 1
    
    assert all(
        len(chunk) <= 900
        for chunk in chunks
    )
    
    
    