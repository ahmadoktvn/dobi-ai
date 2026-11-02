import os
import re
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import requests

from app.embeddings import embed_text
from app.vector_store import VectorStore
from app.system_prompt import (
    SYSTEM_PROMPT_DOBI,
    RECIPES_DATABASE,
    is_greeting_or_chitchat,
    has_culinary_intent,
    build_recipe_context,
    generate_local_fallback_response,
    normalize_text
)

# Inisialisasi FastAPI App
app = FastAPI(
    title="Dobi AI - RAG Smart Recipe Assistant",
    description="Asisten resep masakan pintar berbasis RAG, OpenSearch Vector DB, dan Llama 3.2 3B",
    version="1.0.0"
)

# Konfigurasi Template Jinja2
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Konfigurasi Koneksi Ollama & OpenSearch
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OPENSEARCH_BASE_URL = os.getenv("OPENSEARCH_BASE_URL", "http://opensearch:9200")

# Inisialisasi Vector Store OpenSearch
vector_store = VectorStore(base_url=OPENSEARCH_BASE_URL, index_name="recipes-index")

# ==============================================================================
# RETRIEVER (RAG: OpenSearch Vector Search + Knowledge Base Fallback)
# ==============================================================================
def retrieve_recipe_rag(user_query: str) -> Optional[Dict[str, Any]]:
    """
    Logika Pengambilan Dokumen Resep (RAG):
    1. Sapaan murni ("halo", "hai", dll) -> Jangan ambil resep apa pun!
    2. Cek apakah ada niat kuliner / bahan masakan.
    3. Cari di OpenSearch k-NN Vector DB (999 Resep Cookpad).
    4. Fallback ke basis data resep lokal jika OpenSearch tidak menemukan hasil relevan.
    """
    # Filter 1: Sapaan atau basa-basi santai
    if is_greeting_or_chitchat(user_query):
        return None

    # Tentukan ambang batas skor kemiripan:
    # Jika pengguna menyebutkan bahan/kuliner: ambang batas 0.65
    # Jika pertanyaan umum di luar makanan: ambang batas tinggi 0.82 agar tidak salah mencocokkan resep acak
    has_intent = has_culinary_intent(user_query)
    min_score_threshold = 0.65 if has_intent else 0.82

    # 1. k-NN Semantic Vector Search di OpenSearch
    try:
        query_vector = embed_text(user_query, base_url=OLLAMA_BASE_URL, model=OLLAMA_EMBED_MODEL)
        hits = vector_store.search(query_vector, k=1, min_score=min_score_threshold)
        if hits:
            top_hit = hits[0]
            meta = top_hit.get("metadata", {})
            raw_bahan = meta.get("bahan", "")
            raw_langkah = meta.get("langkah", "")

            # Parsing bahan dan langkah
            if ";" in raw_bahan:
                ingredients = [b.strip() for b in raw_bahan.split(";") if b.strip()]
            else:
                ingredients = [b.strip() for b in raw_bahan.split("\n") if b.strip()]

            steps = [s.strip() for s in raw_langkah.split("\n") if s.strip()]

            return {
                "id": top_hit.get("id"),
                "title": meta.get("judul", "Resep Pilihan"),
                "category": "Koleksi Resep Cookpad",
                "prep_time": "Praktis & Lezat",
                "portion": "Sesuai Porsi",
                "ingredients": ingredients or [raw_bahan],
                "steps": steps or [raw_langkah],
                "tips": f"Resep resmi Cookpad: {meta.get('url', '-')}",
                "url": meta.get("url", ""),
                "score": top_hit.get("score"),
                "source_type": "opensearch_vector_db"
            }
    except Exception:
        pass

    # 2. Fallback pencocokan kata kunci pada resep lokal (hanya jika ada niat kuliner)
    if not has_intent:
        return None

    normalized_query = normalize_text(user_query)
    query_tokens = set(normalized_query.split())
    best_match: Optional[Dict[str, Any]] = None
    highest_score = 0

    for recipe in RECIPES_DATABASE:
        score = 0
        norm_title = normalize_text(recipe["title"])
        if norm_title in normalized_query:
            score += 15
        title_tokens = set(norm_title.split())
        score += len(query_tokens.intersection(title_tokens)) * 4
        for kw in recipe.get("keywords", []):
            norm_kw = normalize_text(kw)
            if norm_kw in normalized_query:
                score += 6
            elif query_tokens.intersection(set(norm_kw.split())):
                score += 2

        if score > highest_score:
            highest_score = score
            best_match = recipe

    if highest_score >= 6 and best_match is not None:
        return best_match

    return None

# ==============================================================================
# PYDANTIC SCHEMAS
# ==============================================================================
class ChatRequest(BaseModel):
    message: str

class ChatStreamRequest(BaseModel):
    messages: List[Dict[str, Any]] = []

class ChatResponse(BaseModel):
    reply: str
    retrieved_recipe: Optional[str] = None
    source: str
    context_used: bool
    url: Optional[str] = None
    score: Optional[float] = None

# ==============================================================================
# ROUTES & ENDPOINTS
# ==============================================================================
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Merender antarmuka web modern Dobi AI."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "recipes": RECIPES_DATABASE,
            "ollama_url": OLLAMA_BASE_URL,
            "model_name": OLLAMA_MODEL
        }
    )

@app.get("/api/recipes")
async def get_recipes():
    """Mengembalikan daftar resep statis dari knowledge base."""
    return {
        "status": "success",
        "total": len(RECIPES_DATABASE),
        "data": [
            {
                "id": r["id"],
                "title": r["title"],
                "category": r["category"],
                "prep_time": r["prep_time"],
                "portion": r["portion"],
                "keywords": r.get("keywords", [])
            }
            for r in RECIPES_DATABASE
        ]
    }

@app.get("/api/vector-store/stats")
async def vector_store_stats():
    """Mengembalikan statistik dokumen di OpenSearch recipes-index."""
    return {
        "status": "success",
        "index_name": vector_store.index_name,
        "total_documents": vector_store.count(),
        "vector_dimension": vector_store.dimension
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """
    Endpoint pemrosesan chat Dobi AI:
    1. Mengidentifikasi niat pengguna & RAG retrieval
    2. Menghubungkan ke Ollama Chat API (/api/chat) dengan role system & user
    3. Otomatis fallback jika Ollama sedang offline
    """
    user_query = payload.message.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong.")

    # 1. RAG Retrieval Step
    matched_recipe = retrieve_recipe_rag(user_query)
    context_used = matched_recipe is not None
    recipe_title = matched_recipe["title"] if matched_recipe else None
    recipe_url = matched_recipe.get("url") if matched_recipe else None
    recipe_score = matched_recipe.get("score") if matched_recipe else None

    # 2. Susun pesan dengan isolasi System Prompt vs User Content
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_DOBI}
    ]

    if matched_recipe:
        recipe_context = build_recipe_context(matched_recipe)
        user_content = f"{recipe_context}\n\nPertanyaan pengguna: {user_query}"
    else:
        user_content = user_query

    messages.append({"role": "user", "content": user_content})

    # 3. Payload untuk Ollama /api/chat
    ollama_payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "num_predict": 400,
            "temperature": 0.7
        }
    }

    try:
        # Kirim request ke Ollama Chat API
        response = requests.post(
            OLLAMA_CHAT_URL,
            json=ollama_payload,
            timeout=120
        )

        if response.status_code == 200:
            result_json = response.json()
            # Ambil respon dari struktur chat Ollama
            reply_text = result_json.get("message", {}).get("content", "").strip()
            if not reply_text:
                reply_text = result_json.get("response", "").strip()

            return ChatResponse(
                reply=reply_text,
                retrieved_recipe=recipe_title,
                source="ollama_chat",
                context_used=context_used,
                url=recipe_url,
                score=recipe_score
            )
        else:
            fallback_text = generate_local_fallback_response(user_query, matched_recipe)
            return ChatResponse(
                reply=fallback_text,
                retrieved_recipe=recipe_title,
                source="local_fallback_on_ollama_error",
                context_used=context_used,
                url=recipe_url,
                score=recipe_score
            )

    except requests.exceptions.RequestException:
        fallback_text = generate_local_fallback_response(user_query, matched_recipe)
        return ChatResponse(
            reply=fallback_text,
            retrieved_recipe=recipe_title,
            source="local_knowledge_base",
            context_used=context_used,
            url=recipe_url,
            score=recipe_score
        )

@app.post("/chat/stream")
async def chat_stream_endpoint(payload: ChatStreamRequest):
    """Endpoint chat streaming: validasi messages tidak boleh kosong."""
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages kosong")
    return {"status": "ok", "message": "chat stream ready"}

@app.get("/health")
async def health_check():
    """Health check endpoint untuk Docker dan monitoring."""
    return {
        "status": "healthy",
        "service": "Dobi AI Recipe Assistant",
        "ollama_chat_target": OLLAMA_CHAT_URL,
        "opensearch_target": OPENSEARCH_BASE_URL,
        "opensearch_recipes_count": vector_store.count(),
        "knowledge_base_recipes": len(RECIPES_DATABASE)
    }
