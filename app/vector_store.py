import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
import httpx

logger = logging.getLogger(__name__)

class VectorStore:
    """
    OpenSearch Vector Store client untuk k-NN Vector Search (Module 12, 13, 14).
    Mendukung pembuatan index k-NN HNSW, indexing dokumen tunggal/bulk, dan semantic search.
    Kompatibel penuh dengan spesifikasi Module 13 & 14 sekaligus aplikasi Dobi AI.
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

    def ensure_index(self, index_name: Optional[str] = None) -> bool:
        """
        Membuat index k-NN di OpenSearch jika belum ada (idempotent).
        Mendukung pemanggilan `ensure_index()` atau `ensure_index('nama-index')`.
        """
        target_index = index_name or self.index_name
        with httpx.Client(timeout=self.timeout) as client:
            check_resp = client.head(f"{self.base_url}/{target_index}")
            if check_resp.status_code == 200:
                logger.info(f"Index '{target_index}' sudah ada di OpenSearch.")
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
            resp = client.put(f"{self.base_url}/{target_index}", json=index_schema)
            if resp.status_code in (200, 201):
                logger.info(f"Berhasil membuat index '{target_index}' di OpenSearch.")
                return True
            else:
                logger.error(f"Gagal membuat index '{target_index}': {resp.status_code} - {resp.text}")
                return False

    def index_document(
        self,
        *args,
        **kwargs
    ) -> bool:
        """
        Menyimpan satu dokumen beserta vektor embedding-nya ke OpenSearch.
        Mendukung 2 gaya pemanggilan:
        1. Module 13 style: index_document(index_name, doc_id, text, embedding, metadata)
        2. Dobi style: index_document(doc_id, text, embedding, metadata)
        """
        # Parsing argumen fleksibel
        if len(args) == 5:
            target_index, doc_id, text, embedding, metadata = args
        elif len(args) == 4:
            if isinstance(args[1], str) and isinstance(args[2], str) and isinstance(args[3], list):
                # index_name, doc_id, text, embedding
                target_index, doc_id, text, embedding = args
                metadata = kwargs.get("metadata", {})
            else:
                # doc_id, text, embedding, metadata
                target_index = self.index_name
                doc_id, text, embedding, metadata = args
        elif len(args) == 3:
            target_index = self.index_name
            doc_id, text, embedding = args
            metadata = kwargs.get("metadata", {})
        else:
            target_index = kwargs.get("index_name", self.index_name)
            doc_id = kwargs.get("doc_id", "")
            text = kwargs.get("text", "")
            embedding = kwargs.get("embedding", [])
            metadata = kwargs.get("metadata", {})

        payload = {
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {}
        }
        with httpx.Client(timeout=self.timeout) as client:
            url = f"{self.base_url}/{target_index}/_doc/{doc_id}?refresh=true"
            resp = client.put(url, json=payload)
            return resp.status_code in (200, 201)

    def bulk_index_documents(self, documents: List[Dict[str, Any]], index_name: Optional[str] = None) -> int:
        """
        Menyimpan dokumen dalam jumlah banyak secara batch menggunakan endpoint _bulk.
        """
        if not documents:
            return 0

        target_index = index_name or self.index_name
        bulk_lines = []
        for doc in documents:
            action = {"index": {"_index": target_index, "_id": str(doc["id"])}}
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
        *args,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Melakukan k-NN Semantic Search terhadap OpenSearch.
        Mendukung 2 gaya pemanggilan:
        1. Module 13 style: search(index_name, query_embedding, k=3)
        2. Dobi style: search(vector, k=3, min_score=0.0)
        
        Hasil yang dikembalikan kompatibel dengan:
        - hit['_source']['text'] (Module 13 & 14)
        - hit['_score'] & hit['_id']
        - hit['text'], hit['score'], hit['metadata'] (Dobi AI)
        """
        if len(args) >= 2 and isinstance(args[0], str):
            target_index = args[0]
            vector = args[1]
            k = args[2] if len(args) > 2 else kwargs.get("k", 3)
            min_score = kwargs.get("min_score", 0.0)
        elif len(args) >= 1 and isinstance(args[0], list):
            target_index = kwargs.get("index_name", self.index_name)
            vector = args[0]
            k = args[1] if len(args) > 1 else kwargs.get("k", 3)
            min_score = kwargs.get("min_score", 0.0)
        else:
            target_index = kwargs.get("index_name", self.index_name)
            vector = kwargs.get("vector", kwargs.get("query_embedding", []))
            k = kwargs.get("k", 3)
            min_score = kwargs.get("min_score", 0.0)

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
            url = f"{self.base_url}/{target_index}/_search"
            resp = client.post(url, json=query_payload)
            if resp.status_code != 200:
                logger.warning(f"Search request failed: {resp.status_code} - {resp.text}")
                return []

            data = resp.json()
            raw_hits = data.get("hits", {}).get("hits", [])
            results = []
            for hit in raw_hits:
                score = hit.get("_score", 0.0)
                if score >= min_score:
                    source_dict = hit.get("_source", {})
                    # Menyediakan struktur gabungan yang mendukung kedua gaya akses
                    unified_hit = {
                        "_id": hit.get("_id"),
                        "_score": score,
                        "_source": source_dict,
                        "id": hit.get("_id"),
                        "score": score,
                        "text": source_dict.get("text", ""),
                        "metadata": source_dict.get("metadata", {})
                    }
                    results.append(unified_hit)
            return results

    def count(self, index_name: Optional[str] = None) -> int:
        """Mengembalikan jumlah total dokumen dalam index."""
        target_index = index_name or self.index_name
        with httpx.Client(timeout=self.timeout) as client:
            url = f"{self.base_url}/{target_index}/_count"
            resp = client.get(url)
            if resp.status_code == 200:
                return resp.json().get("count", 0)
            return 0
