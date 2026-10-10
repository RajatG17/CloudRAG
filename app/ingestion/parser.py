from pathlib import Path

from pypdf import PdfReader


def extract_pages(file_path: Path) -> list[str]:
    """Extract text from all pages of a PDF file.

    Args:
        file_path (Path): The path to the PDF file.

    Returns:
        list[str]: A list containing the text from each page.
    """
    
    suffix = file_path.suffix.lower()
    
    if suffix == ".txt":
        text = file_path.read_text(encoding="utf-8")
        
        return ([(1, text)])
    
    if suffix == ".pdf":
        text = PdfReader(str(file_path))
        
        pages = []
        
        for pg_num, page in enumerate(text.pages, start=1):
            text = page.extract_text() or ""
            
            pages.append((pg_num, text))
            
        return pages
    
    raise ValueError(f"Unsupported file type: {suffix}. Only .txt and .pdf files are supported at the moment.")

