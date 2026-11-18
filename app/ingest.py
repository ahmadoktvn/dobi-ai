import os
from pypdf import PdfReader
from app.embeddings import embed_text
from app.vector_store import VectorStore

def extract_text(file_path: str) -> str:
    """Mengekstrak teks dari file .pdf atau membaca langsung file teks/.md/.json (Module 10)."""
    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def ingest_documents(
    knowledge_base_path: str,
    vector_store: VectorStore,
    index_name: str = "recipes-index",
    ollama_base_url: str = "http://ollama:11434",
) -> int:
    """
    Menyimpan seluruh dokumen dalam folder knowledge base ke OpenSearch (Module 14).
    Menggunakan doc_id=filename sebagai identifier idempotent (overwrite di tempat jika di-ingest ulang).
    """
    vector_store.ensure_index(index_name)
    count = 0
    if not os.path.exists(knowledge_base_path):
        return 0

    for filename in sorted(os.listdir(knowledge_base_path)):
        file_path = os.path.join(knowledge_base_path, filename)
        if not os.path.isfile(file_path):
            continue
        try:
            text = extract_text(file_path)
            if not text.strip():
                continue
            embedding = embed_text(text, base_url=ollama_base_url)
            vector_store.index_document(
                index_name,
                doc_id=filename,
                text=text,
                embedding=embedding,
                metadata={"source": filename},
            )
            count += 1
        except Exception as e:
            print(f"Gagal meng-ingest {filename}: {e}")
            continue

    return count
