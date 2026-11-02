import httpx
from typing import List, Union

def embed_text(text: str, base_url: str, model: str = "nomic-embed-text") -> list[float]:
    with httpx.Client() as client:
        response = client.post(
            f"{base_url}/api/embed",
            json={"model": model, "input": text},
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]

def embed_batch(texts: List[str], base_url: str, model: str = "nomic-embed-text") -> List[List[float]]:
    """Mengirim beberapa teks sekaligus ke Ollama untuk embedding paralel berkecepatan tinggi."""
    if not texts:
        return []
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            f"{base_url}/api/embed",
            json={"model": model, "input": texts},
        )
        response.raise_for_status()
        return response.json()["embeddings"]

