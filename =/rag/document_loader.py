"""Extract and chunk PDF/TXT course material."""
from io import BytesIO
import re
from pypdf import PdfReader

def extract_text(uploaded_file) -> list[dict]:
    raw = uploaded_file.getvalue()
    if not raw: raise ValueError("The uploaded file is empty.")
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        pages = [{"text": page.extract_text() or "", "page": index + 1} for index, page in enumerate(PdfReader(BytesIO(raw)).pages)]
    elif name.endswith(".txt"):
        pages = [{"text": raw.decode("utf-8", errors="ignore"), "page": 1}]
    else: raise ValueError("Please upload a PDF or TXT file.")
    return pages

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def chunk_pages(pages: list[dict], chunk_size: int = 900, overlap: int = 120) -> list[dict]:
    chunks = []
    for page in pages:
        text = clean_text(page["text"])
        for start in range(0, len(text), max(1, chunk_size - overlap)):
            chunk = text[start:start + chunk_size]
            if chunk: chunks.append({"text": chunk, "page": page["page"]})
    return chunks
