import os
import json
import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

class VectorStore:
    """
    OpenSearch Vector Store client untuk k-NN Vector Search (Module 13).
    Mendukung pembuatan index k-NN HNSW, indexing dokumen tunggal/bulk, dan semantic search.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        index_name: str = "recipes-index",
        dimension: int = 768,
        timeout: float = 30.0
    ):
        if base_url is None:
            self.base_url = os.getenv("OPENSEARCH_BASE_URL", "http://opensearch:9200").rstrip("/")
        else:
            self.base_url = base_url.rstrip("/")
        self.index_name = index_name
        self.dimension = dimension
        self.timeout = timeout

    def ensure_index(self) -> bool:
        """Membuat index k-NN di OpenSearch jika belum ada."""
        with httpx.Client(timeout=self.timeout) as client:
            check_resp = client.head(f"{self.base_url}/{self.index_name}")
            if check_resp.status_code == 200:
                logger.info(f"Index '{self.index_name}' sudah ada di OpenSearch.")
                return True

            index_schema = {
                "settings": {
                    "index": {
                        "knn": True,
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    }
                },
                "mappings": {
                    "properties": {
                        "text": {"type": "text"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": self.dimension,
                            "method": {
                                "engine": "nmslib",
                                "space_type": "cosinesimil",
                                "name": "hnsw",
                                "parameters": {
                                    "ef_construction": 128,
                                    "m": 16
                                }
                            }
                        },
                        "metadata": {"type": "object"}
                    }
                }
            }
            resp = client.put(f"{self.base_url}/{self.index_name}", json=index_schema)
            if resp.status_code in (200, 201):
                logger.info(f"Berhasil membuat index '{self.index_name}' di OpenSearch.")
                return True
            else:
                logger.error(f"Gagal membuat index '{self.index_name}': {resp.status_code} - {resp.text}")
                return False

    def index_document(
        self,
        doc_id: str,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Menyimpan satu dokumen beserta vektor embedding-nya ke OpenSearch."""
        payload = {
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {}
        }
        with httpx.Client(timeout=self.timeout) as client:
            url = f"{self.base_url}/{self.index_name}/_doc/{doc_id}?refresh=true"
            resp = client.put(url, json=payload)
            return resp.status_code in (200, 201)

    def bulk_index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Menyimpan dokumen dalam jumlah banyak secara batch menggunakan endpoint _bulk.
        Masing-masing item di `documents` harus memiliki: id, text, embedding, metadata.
        """
        if not documents:
            return 0

        bulk_lines = []
        for doc in documents:
            action = {"index": {"_index": self.index_name, "_id": str(doc["id"])}}
            source = {
                "text": doc["text"],
                "embedding": doc["embedding"],
                "metadata": doc.get("metadata", {})
            }
            bulk_lines.append(json.dumps(action))
            bulk_lines.append(json.dumps(source))

        bulk_payload = "\n".join(bulk_lines) + "\n"

        with httpx.Client(timeout=60.0) as client:
            url = f"{self.base_url}/_bulk?refresh=true"
            resp = client.post(
                url,
                content=bulk_payload,
                headers={"Content-Type": "application/x-ndjson"}
            )
            if resp.status_code in (200, 201):
                res_json = resp.json()
                items = res_json.get("items", [])
                successful = sum(1 for item in items if item.get("index", {}).get("status") in (200, 201))
                return successful
            else:
                logger.error(f"Bulk indexing gagal: {resp.status_code} - {resp.text}")
                return 0

    def search(
        self,
        vector: List[float],
        k: int = 3,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Melakukan k-NN Semantic Search terhadap OpenSearch berdasarkan kemiripan kosinus (Cosine Similarity).
        """
        query_payload = {
            "size": k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": vector,
                        "k": k
                    }
                }
            }
        }
        with httpx.Client(timeout=self.timeout) as client:
            url = f"{self.base_url}/{self.index_name}/_search"
            resp = client.post(url, json=query_payload)
            if resp.status_code != 200:
                logger.warning(f"Search request failed: {resp.status_code} - {resp.text}")
                return []

            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            results = []
            for hit in hits:
                score = hit.get("_score", 0.0)
                if score >= min_score:
                    results.append({
                        "id": hit.get("_id"),
                        "score": score,
                        "text": hit.get("_source", {}).get("text", ""),
                        "metadata": hit.get("_source", {}).get("metadata", {})
                    })
            return results

    def count(self) -> int:
        """Mengembalikan jumlah total dokumen dalam index saat ini."""
        with httpx.Client(timeout=self.timeout) as client:
            url = f"{self.base_url}/{self.index_name}/_count"
            resp = client.get(url)
            if resp.status_code == 200:
                return resp.json().get("count", 0)
            return 0
