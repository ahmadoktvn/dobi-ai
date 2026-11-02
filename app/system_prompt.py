import os
import re
import json
from typing import Optional, Dict, Any, List

# Lokasi file knowledge base
KB_DIR_CANDIDATES = [
    os.getenv("KNOWLEDGE_BASE_PATH", "/app/knowledge-base"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge-base"),
    os.path.join(os.getcwd(), "knowledge-base"),
]

def find_kb_file(filename: str) -> Optional[str]:
    """Mencari lokasi absolut file knowledge base."""
    for kb_dir in KB_DIR_CANDIDATES:
        p = os.path.join(kb_dir, filename)
        if os.path.isfile(p):
            return p
    return None

def load_system_prompt() -> str:
    """Membaca instruksi system prompt dari knowledge-base/system_prompt.txt."""
    file_path = find_kb_file("system_prompt.txt")
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception:
            pass

    # Fallback string jika file belum terbaca
    return (
        "Kamu adalah 'Dobi AI', asisten koki pintar yang ramah, santun, dan natural.\n"
        "Jawab pertanyaan pengguna secara wajar, ramah, dan bersahabat.\n"
        "Jika pengguna hanya menyapa, sambut dan tanyakan bahan apa yang dipunya atau resep apa yang dicari.\n"
        "Jika pertanyaan umum di luar masakan (seperti siapa presiden, pengetahuan umum), jawab akurat dan singkat, lalu arahkan kembali dengan ramah untuk menanyakan resep masakan.\n"
        "Jika pertanyaan resep, sajikan bahan dan langkah memasak secara rapi dan sistematis."
    )

def load_recipes_database() -> List[Dict[str, Any]]:
    """Membaca data resep statis dari knowledge-base/recipes.json."""
    file_path = find_kb_file("recipes.json")
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

# Muat sistem prompt dan data resep
SYSTEM_PROMPT_DOBI = load_system_prompt()
RECIPES_DATABASE = load_recipes_database()

# Kata sapaan & basa-basi umum
GREETING_WORDS = {
    "halo", "hallo", "hai", "hi", "hey", "hei", "helo", "p", "assalamualaikum",
    "pagi", "siang", "sore", "malam", "selamat pagi", "selamat siang", "selamat sore", "selamat malam",
    "tes", "test", "testing", "ping", "kamu siapa", "siapa kamu", "terima kasih", "makasih", "thanks", "ok", "oke", "siap",
    "apa kabar", "gimana kabarnya", "bisa apa", "kamu bisa apa", "bisa apa saja", "assalamu'alaikum"
}

# Kata kunci niat kuliner & bahan masakan
RECIPE_INTENT_KEYWORDS = [
    "resep", "masak", "cara buat", "cara membuat", "bumbu", "bahan", "punya", "ada",
    "makanan", "kuliner", "goreng", "rebus", "tumis", "panggang", "bakar", "sayur",
    "sop", "soto", "ayam", "daging", "sapi", "kambing", "ikan", "udang", "cumi",
    "telur", "tahu", "tempe", "nasi", "mie", "sambal", "camilan", "sarapan", "menu",
    "diet", "enak", "bikin", "olahan", "kukus", "pedas", "manis", "asin", "gurih",
    "singkong", "kue", "roti", "keju", "dapur", "koki", "chef", "porsi"
]

def normalize_text(text: str) -> str:
    """Normalisasi teks dengan mengubah ke lowercase dan menghilangkan tanda baca."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return text.strip()

def is_greeting_or_chitchat(query: str) -> bool:
    """Mendeteksi apakah pesan pengguna hanya berupa sapaan atau obrolan santai tanpa niat resep."""
    norm = normalize_text(query)
    if not norm or norm in GREETING_WORDS:
        return True
    tokens = norm.split()
    if len(tokens) <= 3 and any(t in GREETING_WORDS for t in tokens):
        if not any(k in norm for k in RECIPE_INTENT_KEYWORDS):
            return True
    return False

def has_culinary_intent(query: str) -> bool:
    """Mendeteksi apakah pengguna menyebutkan kata kunci kuliner, bahan, atau resep."""
    norm = normalize_text(query)
    return any(k in norm for k in RECIPE_INTENT_KEYWORDS)

def build_recipe_context(retrieved_recipe: Optional[Dict[str, Any]]) -> str:
    """Membuat blok konteks resep terstruktur untuk disuntikkan ke Llama 3.2 3B."""
    if not retrieved_recipe:
        return ""

    ingredients_formatted = "\n".join([f"- {item}" for item in retrieved_recipe["ingredients"]])
    steps_formatted = "\n".join([f"{idx+1}. {step}" for idx, step in enumerate(retrieved_recipe["steps"])])
    url_info = f"\nTautan Sumber Asli Cookpad: {retrieved_recipe.get('url')}" if retrieved_recipe.get("url") else ""

    return f"""Berikut data resep resmi yang ditarik dari database untuk menjawab pertanyaan pengguna:

[DATA RESEP TERPILIH]
Judul Resep : {retrieved_recipe['title']}
Kategori    : {retrieved_recipe['category']}
Estimasi Waktu : {retrieved_recipe['prep_time']}
Porsi       : {retrieved_recipe['portion']}{url_info}

Bahan-Bahan:
{ingredients_formatted}

Langkah Memasak:
{steps_formatted}

Tips Koki Dobi:
{retrieved_recipe['tips']}
[AKHIR DATA RESEP]"""

def generate_local_fallback_response(user_query: str, recipe: Optional[Dict[str, Any]]) -> str:
    """Respon cerdas, natural, dan ramah jika Ollama lokal sedang offline atau lambat."""
    if recipe:
        ingredients_list = "\n".join([f"• {b}" for b in recipe["ingredients"]])
        steps_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(recipe["steps"])])
        url_line = f"\n🔗 **Tautan Resep Asli Cookpad:** [{recipe.get('url')}]({recipe.get('url')})\n" if recipe.get("url") else ""
        source_note = "Vector Database OpenSearch (999 Resep Cookpad)" if recipe.get("source_type") == "opensearch_vector_db" else "Knowledge Base Lokal Dobi AI"

        return (
            f"Halo Sobat Dapur! 👨‍🍳 Aku **Dobi AI**.\n\n"
            f"> 💡 *(Catatan: Mode Cepat Aktif - Resep ditarik dari {source_note})*\n\n"
            f"Berikut adalah panduan lengkap untuk membuat **{recipe['title']}**:\n\n"
            f"⏱️ **Estimasi Waktu:** {recipe['prep_time']} | 🍽️ **Porsi:** {recipe['portion']}\n"
            f"{url_line}\n"
            f"### 🛒 Bahan-Bahan:\n{ingredients_list}\n\n"
            f"### 🍳 Cara Memasak:\n{steps_list}\n\n"
            f"### 💡 Tips Koki Dobi AI:\n{recipe['tips']}\n\n"
            f"Selamat mencoba di dapur ya! Jika ada bahan yang ingin diganti atau ditanyakan, kabari Dobi ya! 🔥"
        )
    else:
        norm = normalize_text(user_query)
        if is_greeting_or_chitchat(user_query):
            return (
                "Halo Sobat Dapur! 👨‍🍳 Senang bertemu denganmu! Aku **Dobi AI**, asisten koki pintar kamu.\n\n"
                "Hari ini kamu lagi ada bahan apa di kulkas atau ingin ide resep apa? "
                "Cukup tuliskan bahannya (misalnya: *'punya telur, tahu, dan kecap'* atau *'resep soto ayam'*), "
                "nanti Dobi carikan resep terbaik dari 999 database resep Cookpad! ✨"
            )
        elif "presiden" in norm:
            return (
                "Presiden Republik Indonesia saat ini adalah Bapak **Prabowo Subianto** (didampingi Wakil Presiden Gibran Rakabuming Raka). 🇮🇩\n\n"
                "Nah, kalau urusan menu masakan lezat di rumah, serahkan ke Dobi ya! Kamu lagi punya bahan apa di dapur atau mau rekomendasi resep apa hari ini? 🍳"
            )
        elif "bisa apa" in norm or "kamu siapa" in norm:
            return (
                "Aku adalah **Dobi AI**, asisten koki pintar kamu! 👨‍🍳 Aku siap membantumu:\n\n"
                "1. **Mencari ide masakan** berdasarkan sisa bahan yang ada di kulkas atau dapurmu.\n"
                "2. **Menyajikan resep lengkap** dengan takaran bumbu dan langkah memasak dari 999 koleksi resep Cookpad terverifikasi.\n"
                "3. **Memberikan tips dapur**, pengganti bahan, dan panduan anti-gagal.\n\n"
                "Coba sebutkan bahan yang kamu punya saat ini, yuk kita masak! 🥘"
            )
        else:
            return (
                f"Halo! 👨‍🍳 Menanggapi pertanyaanmu tentang *\"{user_query}\"*, spesialisasiku sebagai Dobi AI adalah seputar resep masakan dan urusan dapur.\n\n"
                f"Coba sebutkan bahan yang kamu punya di rumah (contoh: *'punya ayam dan bawang'* atau *'resep nasi goreng'*), "
                f"dan Dobi akan langsung carikan resep paling lezat untukmu! 🥘"
            )
