from .vector_store import VectorStore

def retrieve_context(question: str, limit: int = 5) -> tuple[str, list[dict]]:
    results = VectorStore().search(question, limit)
    context = "\n\n".join(f"[{item['metadata']['filename']}, page {item['metadata']['page']}] {item['text']}" for item in results)
    return context, results
