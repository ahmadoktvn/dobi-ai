import os
import csv
import sys
import time
from typing import List, Dict, Any
from app.embeddings import embed_batch, embed_text
from app.vector_store import VectorStore

def get_csv_path() -> str:
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "dataset_resep.csv"),
        "/app/data/dataset_resep.csv",
        "data/dataset_resep.csv",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("File data/dataset_resep.csv tidak ditemukan di jalur yang diharapkan.")

def load_clean_recipes(csv_path: str, limit: int = None) -> List[Dict[str, str]]:
    recipes = []
    with open(csv_path, mode="r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            judul = row.get("Judul", "").strip()
            bahan = row.get("Bahan-Bahan", "").strip()
            langkah = row.get("Langkah-Langkah", "").strip()
            url = row.get("URL", "").strip()

            # Filter data kosong atau placeholder 'Tanpa Judul'
            if not judul or judul == "Tanpa Judul" or not bahan or not langkah:
                continue

            recipes.append({
                "id": f"recipe-{idx+1}",
                "judul": judul,
                "bahan": bahan,
                "langkah": langkah,
                "url": url
            })

            if limit and len(recipes) >= limit:
                break

    return recipes

def run_ingest(batch_size: int = 25, limit: int = None):
    print("=" * 60)
    print("🍳 DOBI AI - INGESTION DATASET RESEP KE VECTOR DB (OPENSEARCH)")
    print("=" * 60)

    csv_path = get_csv_path()
    print(f"📁 Membaca file: {csv_path}")

    recipes = load_clean_recipes(csv_path, limit=limit)
    total_recipes = len(recipes)
    print(f"✅ Ditemukan {total_recipes} resep valid siap diproses.\n")

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    opensearch_url = os.getenv("OPENSEARCH_BASE_URL", "http://opensearch:9200")

    print(f"🔗 Menghubungkan ke OpenSearch di {opensearch_url}...")
    vector_store = VectorStore(base_url=opensearch_url, index_name="recipes-index")
    if not vector_store.ensure_index():
        print("❌ Gagal membuat atau memeriksa index di OpenSearch. Pastikan container opensearch aktif!")
        return

    print(f"🔗 Menghubungkan ke Ollama di {ollama_url} (Model: nomic-embed-text)...")
    start_time = time.time()
    indexed_count = 0

    for i in range(0, total_recipes, batch_size):
        batch = recipes[i:i + batch_size]
        batch_texts = []
        batch_docs = []

        for item in batch:
            # Format teks optimal untuk embedding semantik bahan & nama masakan
            formatted_text = (
                f"Judul: {item['judul']}\n"
                f"Bahan-bahan: {item['bahan']}\n"
                f"Cara Memasak:\n{item['langkah']}"
            )
            batch_texts.append(formatted_text)

        # 1. Generate Embeddings (batch via Ollama)
        try:
            embeddings = embed_batch(batch_texts, base_url=ollama_url)
        except Exception as e:
            print(f"\n⚠️ Batch embed gagal, mencoba single embed fallback: {e}")
            embeddings = []
            for t in batch_texts:
                try:
                    embeddings.append(embed_text(t, base_url=ollama_url))
                except Exception as inner_e:
                    print(f"❌ Gagal embed item: {inner_e}")
                    embeddings.append([0.0] * 768)

        # 2. Siapkan dokumen untuk OpenSearch
        for item, text, emb in zip(batch, batch_texts, embeddings):
            batch_docs.append({
                "id": item["id"],
                "text": text,
                "embedding": emb,
                "metadata": {
                    "judul": item["judul"],
                    "bahan": item["bahan"],
                    "langkah": item["langkah"],
                    "url": item["url"]
                }
            })

        # 3. Simpan ke OpenSearch via bulk index
        success = vector_store.bulk_index_documents(batch_docs)
        indexed_count += success

        progress = (min(i + batch_size, total_recipes) / total_recipes) * 100
        print(f"⏳ Progress: [{min(i + batch_size, total_recipes):4d}/{total_recipes:4d}] ({progress:5.1f}%) resep berhasil diindeks.")

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"🎉 SELESAI! {indexed_count} dari {total_recipes} resep berhasil tersimpan di OpenSearch.")
    print(f"⏱️ Waktu total: {elapsed:.2f} detik (~{elapsed/60:.2f} menit).")
    print(f"📊 Total dokumen di index: {vector_store.count()} dokumen.")
    print("=" * 60)

if __name__ == "__main__":
    limit_arg = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        limit_arg = int(sys.argv[1])
        print(f"ℹ️ Menjalankan dengan batasan: {limit_arg} resep pertama.")
    run_ingest(batch_size=20, limit=limit_arg)
