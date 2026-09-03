"""ChromaDB storage with OpenAI embeddings."""
import os
from pathlib import Path
import chromadb
from openai import OpenAI

CHROMA_PATH = Path(__file__).resolve().parent.parent / ".chroma"
class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        self.collection = self.client.get_or_create_collection("course_material")
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.openai.embeddings.create(model="text-embedding-3-small", input=texts)
        return [item.embedding for item in response.data]
    def add(self, chunks: list[dict], filename: str, course: str, topic: str = "General") -> int:
        if not chunks: return 0
        ids = [f"{filename}:{i}" for i in range(len(chunks))]
        embeddings = self.embed([chunk["text"] for chunk in chunks])
        self.collection.upsert(ids=ids, documents=[chunk["text"] for chunk in chunks], embeddings=embeddings, metadatas=[{"filename": filename, "page": chunk["page"], "course": course, "topic": topic} for chunk in chunks])
        return len(chunks)
    def search(self, query: str, limit: int = 5) -> list[dict]:
        if self.collection.count() == 0: return []
        result = self.collection.query(query_embeddings=self.embed([query]), n_results=limit)
        return [{"text": text, "metadata": metadata} for text, metadata in zip(result["documents"][0], result["metadatas"][0])]
