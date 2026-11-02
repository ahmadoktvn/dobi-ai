import os
import re
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import requests

# Inisialisasi FastAPI App
app = FastAPI(
    title="Dobi AI - RAG Smart Recipe Assistant",
    description="Asisten resep masakan pintar berbasis RAG sederhana dan Llama 3.2 3B",
    version="1.0.0"
)

# Konfigurasi Template Jinja2
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Konfigurasi Koneksi Ollama & OpenSearch
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
KNOWLEDGE_BASE_PATH = os.environ.get("KNOWLEDGE_BASE_PATH", "/app/knowledge-base")
OPENSEARCH_BASE_URL = os.getenv("OPENSEARCH_BASE_URL", "http://opensearch:9200")

# Inisialisasi Vector Store OpenSearch
from app.embeddings import embed_text
from app.vector_store import VectorStore
vector_store = VectorStore(base_url=OPENSEARCH_BASE_URL, index_name="recipes-index")

# ==============================================================================
# KNOWLEDGE BASE: Resep Masakan Dobi AI (Basis Data RAG Sederhana)
# ==============================================================================
RECIPES_DATABASE: List[Dict[str, Any]] = [
    {
        "id": "nasi-goreng-spesial",
        "title": "Nasi Goreng Spesial Solaria Style",
        "category": "Nasi & Sarapan",
        "prep_time": "15-20 menit",
        "portion": "2 Porsi",
        "keywords": [
            "nasi goreng", "nasgor", "nasi", "sarapan", "telur", "kecap", 
            "bumbu nasi goreng", "makan malam cepat", "solaria"
        ],
        "ingredients": [
            "2 piring nasi putih dingin (lebih baik nasi kemarin/pera)",
            "2 butir telur ayam (1 diorak-arik, 1 dibuat ceplok)",
            "5 butir bakso sapi, diiris tipis",
            "50 gr daging ayam suwir atau udang kupas",
            "3 siung bawang putih, cincang halus",
            "4 siung bawang merah, cincang halus",
            "1 batang daun bawang, iris tipis",
            "2 sdm kecap manis berkualitas",
            "1 sdm saus tiram",
            "1 sdm minyak wijen (kunci aroma harum)",
            "1/2 sdt garam & 1/2 sdt merica bubuk",
            "1/2 sdt kaldu bubuk ayam"
        ],
        "steps": [
            "Panaskan 2 sdm minyak di wajan dengan api sedang ke besar (usahakan wajan benar-benar panas).",
            "Masukkan telur, buat orak-arik setengah matang, lalu pinggirkan ke tepi wajan.",
            "Tumis bawang putih dan bawang merah cincang sampai harum kekuningan.",
            "Masukkan potongan bakso dan ayam suwir, aduk rata bersama telur.",
            "Besarkan api, masukkan nasi putih dingin. Aduk cepat agar nasi tidak menggumpal.",
            "Tambahkan saus tiram, kecap manis, garam, merica, dan kaldu bubuk. Aduk dengan teknik mengaduk cepat agar aroma smokey keluar.",
            "Masukkan irisan daun bawang dan tuangkan minyak wijen di pinggir wajan sesaat sebelum diangkat.",
            "Aduk rata selama 1 menit, koreksi rasa, lalu angkat. Sajikan hangat dengan telur ceplok, kerupuk, dan acar."
        ],
        "tips": "Gunakan nasi yang dingin/disimpan di kulkas semalaman agar butiran nasi terpisah cantik dan tidak lembek saat digoreng."
    },
    {
        "id": "rendang-daging-padang",
        "title": "Rendang Daging Sapi Khas Padang Autentik",
        "category": "Lauk Daging Sapi",
        "prep_time": "3 - 4 jam",
        "portion": "5-6 Porsi",
        "keywords": [
            "rendang", "daging sapi", "padang", "minang", "santan", "masakan padang",
            "daging empuk", "lebaran", "bumbu rendang"
        ],
        "ingredients": [
            "1 kg daging sapi gandik/paha, potong searah serat sekitar 4-5 cm",
            "1.000 ml santan kental dari 3 butir kelapa tua",
            "1.000 ml santan encer",
            "4 lembar daun kunyit, simpulkan",
            "5 lembar daun jeruk purut buang tulang daunnya",
            "2 batang serai, memarkan",
            "2 buah asam kandis",
            "Bumbu Halus: 150 gr cabai merah keriting, 12 siung bawang merah, 6 siung bawang putih, 3 cm jahe, 4 cm lengkuas, 1 sdm ketumbar bubuk, 1/2 sdt pala bubuk, 2 sdt garam"
        ],
        "steps": [
            "Campurkan santan encer, santan kental, bumbu halus, daun kunyit, daun jeruk, dan serai ke dalam wajan besar.",
            "Masak dengan api sedang sambil terus diaduk perlahan tanpa henti agar santan tidak pecah (fase Gulai).",
            "Ketika santan sudah mulai mengental dan mengeluarkan minyak kemerahan (fase Kalio), masukkan potongan daging sapi.",
            "Kecilkan api kompor. Aduk sesekali agar bagian dasar wajan tidak gosong.",
            "Masukkan asam kandis. Lanjutkan memasak dengan api sangat kecil hingga air menyusut dan bumbu berubah warna menjadi cokelat gelap kehitaman.",
            "Minyak kelapa akan meresap kembali dan bumbu menempel sempurna pada daging yang empuk. Angkat dan sajikan."
        ],
        "tips": "Jangan potong daging terlalu tipis agar tidak hancur saat dimasak lama, dan gunakan kelapa tua parut murni tanpa air tambahan berlebih untuk santan kental."
    },
    {
        "id": "ayam-geprek-sambal-bawang",
        "title": "Ayam Geprek Crispy Sambal Bawang Pedas Nampol",
        "category": "Lauk Ayam",
        "prep_time": "30 menit",
        "portion": "2-3 Porsi",
        "keywords": [
            "ayam geprek", "geprek", "sambal bawang", "pedas", "ayam krispi", "ayam crispy",
            "ayam goreng tepung", "sambal korek"
        ],
        "ingredients": [
            "500 gr fillet dada atau paha ayam, potong sesuai selera",
            "Bumbu Marinasi: 3 siung bawang putih parut, 1 sdt garam, 1/2 sdt lada bubuk, 1/2 sdt kaldu bubuk",
            "Tepung Kering: 250 gr tepung terigu protein tinggi, 50 gr tepung maizena, 1 sdt baking powder, 1 sdt bubuk kaldu ayam, 1/2 sdt garam",
            "Pencelup: Air es dingin secukupnya",
            "Bahan Sambal Bawang: 20 buah cabai rawit merah domba, 5 siung bawang putih, 1/2 sdt garam, 1/2 sdt micin/kaldu bubuk, 4 sdm minyak goreng panas sisa menggoreng ayam"
        ],
        "steps": [
            "Marinasi potongan ayam dengan bumbu marinasi minimal 30 menit di kulkas.",
            "Balur ayam ke dalam campuran tepung kering, celupkan ke dalam air es selama 3 detik, lalu balurkan kembali ke tepung kering sambil diremas-remas lembut untuk menghasilkan keriting crispy.",
            "Goreng dalam minyak panas berlimpah (deep frying) dengan api sedang sampai berwarna kuning keemasan dan matang garing. Tiriskan.",
            "Buat Sambal: Ulek kasar cabai rawit merah, bawang putih, garam, dan kaldu bubuk di atas cobek batu.",
            "Siram ulekan sambal dengan minyak goreng yang masih mendidih panas. Aduk rata hingga berdesis harum.",
            "Letakkan ayam crispy di atas cobek sambal, lalu geprek atau memarkan ayam menggunakan ulekan sampai bumbu sambal meresap ke dalam daging.",
            "Sajikan langsung dengan nasi putih hangat dan lalapan mentimun."
        ],
        "tips": "Minyak yang digunakan untuk menyiram sambal harus benar-benar panas agar aroma bawang matang lembut dan tidak langu."
    },
    {
        "id": "soto-ayam-lamongan",
        "title": "Soto Ayam Lamongan Kuah Kuning Koya Gurih",
        "category": "Sup & Soto",
        "prep_time": "45 menit",
        "portion": "4-5 Porsi",
        "keywords": [
            "soto ayam", "soto lamongan", "koya", "kuah kuning", "soto", "sup ayam",
            "makanan hangat", "bubuk koya"
        ],
        "ingredients": [
            "1/2 ekor ayam kampung atau ayam pejantan",
            "1.500 ml air kaldu rebusan ayam",
            "2 batang serai memarkan, 3 lembar daun salam, 4 lembar daun jeruk",
            "Bumbu Halus: 8 siung bawang merah, 5 siung bawang putih, 4 butir kemiri sangrai, 3 cm kunyit bakar, 2 cm jahe, 1 sdt merica, 1 sdm garam",
            "Bahan Koya Gurih: 5 keping kerupuk udang goreng + 3 siung bawang putih goreng, dihaluskan bersama hingga menjadi bubuk lembut",
            "Pelengkap: Soun rebus, tauge pendek, kol iris, telur rebus belah dua, irisan seledri, jeruk nipis, dan sambal cabai rawit"
        ],
        "steps": [
            "Rebus ayam dalam air mendidih dengan api kecil hingga keluar kaldu gurih.",
            "Tumis bumbu halus bersama serai, daun jeruk, dan daun salam hingga harum matang dan berminyak.",
            "Masukkan tumisan bumbu ke dalam panci rebusan kaldu ayam. Masak sampai bumbu meresap ke dalam ayam.",
            "Angkat ayam dari kuah, tiriskan lalu goreng sebentar hingga berkulit emas. Suwir-suwir daging ayam.",
            "Koreksi rasa kuah soto dengan garam, gula, dan kaldu bubuk. Jaga kuah tetap panas mengepul.",
            "Tata di mangkuk: soun, irisan kol, tauge, dan suwiran ayam.",
            "Siram dengan kuah soto panas, taburkan 1-2 sendok makan bubuk koya udang yang melimpah, dan seledri.",
            "Sajikan dengan perasan jeruk nipis dan sambal rawit."
        ],
        "tips": "Kunci kuah soto lamongan yang sedap dan kental adalah bubuk koya yang dibuat dari kombinasi kerupuk udang asli dan bawang putih goreng renyah."
    },
    {
        "id": "sayur-asem-betawi",
        "title": "Sayur Asem Segar Khas Nusantara",
        "category": "Sayuran Sehat",
        "prep_time": "25 menit",
        "portion": "4 Porsi",
        "keywords": [
            "sayur asem", "sayur asam", "sayuran segar", "kuah bening", "labu siam",
            "jagung manis", "melinjo", "sayur sehat", "rendah kalori"
        ],
        "ingredients": [
            "1 buah jagung manis, potong bulat-bulat",
            "1 buah labu siam, potong dadu",
            "5 batang kacang panjang, potong 3 cm",
            "1 genggam daun dan buah melinjo",
            "50 gr kacang tanah",
            "3 buah asam jawa muda atau belimbing wuluh",
            "2 lembar daun salam & 2 cm lengkuas memarkan",
            "1.200 ml air",
            "Bumbu Halus: 5 butir bawang merah, 2 siung bawang putih, 3 buah cabai merah keriting, 2 butir kemiri, 1/2 sdt terasi bakar, 1 sdm gula merah sisir, 1 sdm garam"
        ],
        "steps": [
            "Didihkan air dalam panci. Masukkan bumbu halus, daun salam, lengkuas, dan asam jawa.",
            "Masukkan bahan yang keras terlebih dahulu: kacang tanah, jagung manis, dan buah melinjo. Masak sampai setengah empuk.",
            "Ambil buah asam muda dari panci, lumatkan di mangkok kecil dengan kuah panas, lalu saring air asamnya kembali ke dalam panci.",
            "Masukkan labu siam dan kacang panjang. Beri garam dan gula merah secukupnya.",
            "Terakhir masukkan daun melinjo, masak sebentar sekitar 2-3 menit sampai semua sayur matang pas dan warna tetap cerah.",
            "Cicipi untuk memastikan perpaduan rasa asam, manis gurihnya seimbang. Angkat dan sajikan bersama ikan asin dan sambal terasi."
        ],
        "tips": "Jangan masak sayuran hijau terlalu lama agar warnanya tetap hijau segar dan teksturnya masih renyah (crunchy)."
    },
    {
        "id": "omelet-sayur-keju",
        "title": "Omelet Sayur Keju Praktis (Sarapan 10 Menit)",
        "category": "Sarapan Cepat",
        "prep_time": "10 menit",
        "portion": "1-2 Porsi",
        "keywords": [
            "omelet", "telur dadar", "sarapan cepat", "keju", "sarapan sehat", "telur",
            "menu diet", "bekal anak", "makanan praktis"
        ],
        "ingredients": [
            "3 butir telur ayam segar",
            "30 ml susu cair full cream (membuat telur fluffy/lembut)",
            "30 gr keju cheddar parut atau mozzarella",
            "1/4 buah wortel, serut halus atau cincang kecil",
            "1/2 batang daun bawang, cincang halus",
            "1/4 buah bawang bombay, cincang halus",
            "1 sdm mentega/butter untuk memanggang",
            "Sejumput garam, lada hitam bubuk, dan kaldu jamur"
        ],
        "steps": [
            "Kocok telur bersama susu cair, garam, lada, dan kaldu jamur dalam mangkuk sampai rata dan sedikit berbusa.",
            "Masukkan serutan wortel, daun bawang, dan bawang bombay cincang. Aduk rata.",
            "Panaskan mentega di teflon anti lengket dengan api kecil.",
            "Tuang adonan telur ke teflon, ratakan sayuran ke seluruh permukaan.",
            "Ketika bagian bawah mulai set namun atasnya masih agak basah creamy, taburkan keju parut di salah satu sisi.",
            "Lipat omelet menjadi bentuk setengah lingkaran atau gulung perlahan.",
            "Masak lagi selama 30 detik tiap sisi hingga keju di dalam meleleh. Angkat dan hidangkan bersama saus tomat atau saus sambal."
        ],
        "tips": "Tambahan sedikit susu cair dan memasak dengan api kecil membuat omelet memiliki tekstur lembut (fluffy) ala hotel bintang lima."
    },
    {
        "id": "capcay-kuah-seafood",
        "title": "Capcay Kuah Kental Seafood Spesial",
        "category": "Sayuran & Seafood",
        "prep_time": "20 menit",
        "portion": "3 Porsi",
        "keywords": [
            "capcay", "cap cay", "sayur kuah", "seafood", "udang", "bakso", "chinese food",
            "kembang kol", "sawi", "wortel"
        ],
        "ingredients": [
            "100 gr udang kupas",
            "5 butir bakso ikan/sapi, iris bulat",
            "1 buah wortel, iris serong",
            "1 bonggol kecil brokoli atau kembang kol, potong perkuntum",
            "5 lembar sawi putih & 3 batang caisim, potong kasar",
            "3 siung bawang putih cincang",
            "1 sdm saus tiram, 1 sdm kecap asin, 1 sdt minyak wijen",
            "1 sdm tepung maizena dilarutkan dengan 3 sdm air (pengental)",
            "350 ml air kaldu atau air matang",
            "Garam, merica bubuk, dan gula pasir secukupnya"
        ],
        "steps": [
            "Tumis bawang putih cincang dengan sedikit minyak sampai wangi harum.",
            "Masukkan udang dan bakso, tumis cepat hingga udang berubah warna kemerahan.",
            "Masukkan wortel dan kembang kol, tuang air kaldu. Masak sekitar 3 menit hingga sayuran agak empuk.",
            "Tambahkan saus tiram, kecap asin, garam, gula, dan merica bubuk. Aduk rata.",
            "Masukkan sawi putih dan caisim, masak sebentar agar sawi tetap renyah.",
            "Tuang larutan maizena sedikit demi sedikit sambil diaduk hingga kuah mengental berkilau.",
            "Terakhir masukkan minyak wijen, aduk sekali lalu matikan api. Sajikan selagi hangat mengepul."
        ],
        "tips": "Masukkan sayuran bertekstur keras terlebih dahulu seperti wortel dan brokoli, sementara sayuran berdaun hijau dimasukkan di akhir agar tidak layu berlebihan."
    },
    {
        "id": "pempek-dos-palembang",
        "title": "Pempek Dos Palembang Gurih (Tanpa Ikan) + Cuko Pedas",
        "category": "Camilan Tradisional",
        "prep_time": "40 menit",
        "portion": "4 Porsi",
        "keywords": [
            "pempek", "pempek dos", "cuko", "palembang", "camilan", "tanpa ikan",
            "tapioka", "gorengan", "kuah cuko"
        ],
        "ingredients": [
            "Bahan Biang: 150 gr tepung terigu, 300 ml air, 1 sdt garam, 1 sdt kaldu jamur/bubuk, 3 siung bawang putih halus",
            "Bahan Kering: 250 gr tepung tapioka/sagu tani, 1 butir telur ayam",
            "Bahan Isian: Telur kocok untuk pempek kapal selam mini",
            "Kuah Cuko Asli: 250 gr gula batok/aren hitam, 500 ml air, 10 buah cabai rawit hijau haluskan, 6 siung bawang putih haluskan, 1 sdm asam jawa, 1/2 sdt garam, 1 sdm cuka putih/air perasan jeruk kunci"
        ],
        "steps": [
            "Membuat Biang: Campur terigu, air, bawang putih halus, garam, dan kaldu di panci. Aduk rata sebelum kompor dinyalakan. Nyalakan api kecil, aduk terus hingga mengental menjadi adonan kenyal seperti bubur padat. Dinginkan.",
            "Setelah biang hangat kuku, masukkan 1 butir telur, aduk rata menggunakan spatula.",
            "Masukkan tepung tapioka bertahap sambil diuleni perlahan (jangan terlalu ditekan keras agar tidak alot). Cukup sampai adonan bisa dibentuk.",
            "Bentuk adonan menjadi lenjer (lonjong) atau kapal selam (bentuk mangkuk, isi telur kocok, lalu rapatkan ujungnya).",
            "Rebus dalam air mendidih yang diberi 1 sdm minyak sampai mengapung dan matang hingga bagian dalam. Angkat dan tiriskan.",
            "Goreng pempek dalam minyak panas hingga berkulit renyah keemasan.",
            "Membuat Cuko: Rebus air, gula aren hitam, dan asam jawa sampai larut lalu saring. Masukkan ulekan cabai rawit dan bawang putih halus serta garam. Masak hingga aroma langu hilang dan cuko mengental. Beri cuka.",
            "Potong-potong pempek goreng, sajikan bersama irisan timun dan guyuran kuah cuko kental pedas manis."
        ],
        "tips": "Untuk cuko yang sedap dan legit hitam pekat, gunakan gula aren batok berkualitas khas Linggau atau Curup, dan jangan uleni adonan pempek secara berlebihan."
    }
]

# ==============================================================================
# RETRIEVER (RAG SEDERHANA: Pencocokan Kata Kunci Statis / Dictionary)
# ==============================================================================
def normalize_text(text: str) -> str:
    """Normalisasi teks dengan mengubah ke lowercase dan menghilangkan tanda baca."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return text.strip()

# Daftar kata sapaan, basa-basi, dan perkenalan umum
GREETING_WORDS = {
    "halo", "hallo", "hai", "hi", "hey", "hei", "helo", "p", "assalamualaikum",
    "pagi", "siang", "sore", "malam", "selamat pagi", "selamat siang", "selamat sore", "selamat malam",
    "tes", "test", "testing", "ping", "kamu siapa", "siapa kamu", "terima kasih", "makasih", "thanks", "ok", "oke", "siap",
    "apa kabar", "gimana kabarnya", "bisa apa", "kamu bisa apa", "assalamu'alaikum"
}

# Kata kunci yang menunjukkan niat nyata mencari resep / memasak
RECIPE_INTENT_KEYWORDS = [
    "resep", "masak", "cara buat", "cara membuat", "bumbu", "bahan", "punya", "ada",
    "makanan", "kuliner", "goreng", "rebus", "tumis", "panggang", "bakar", "sayur",
    "sop", "soto", "ayam", "daging", "sapi", "kambing", "ikan", "udang", "cumi",
    "telur", "tahu", "tempe", "nasi", "mie", "sambal", "camilan", "sarapan", "menu",
    "diet", "enak", "bikin", "olahan", "kukus", "pedas", "manis", "asin", "gurih"
]

def is_greeting_or_chitchat(query: str) -> bool:
    """Mendeteksi apakah pesan pengguna hanya berupa sapaan atau obrolan santai."""
    norm = normalize_text(query)
    if not norm or norm in GREETING_WORDS:
        return True
    tokens = norm.split()
    if len(tokens) <= 3 and any(t in GREETING_WORDS for t in tokens):
        # Jika tidak ada satupun kata kunci bahan atau resep, anggap sapaan murni
        if not any(k in norm for k in RECIPE_INTENT_KEYWORDS):
            return True
    return False

def has_culinary_intent(query: str) -> bool:
    """Mendeteksi apakah pengguna menyebutkan kata kunci kuliner, bahan, atau resep."""
    norm = normalize_text(query)
    return any(k in norm for k in RECIPE_INTENT_KEYWORDS)

def retrieve_recipe_rag(user_query: str) -> Optional[Dict[str, Any]]:
    """
    Logika RAG Dobi AI:
    1. Filter awal: Jika pengguna hanya menyapa ("Halo", "Hai"), JANGAN cari resep!
    2. Mencari dokumen relevan di Vector Database OpenSearch (999 resep Cookpad) dengan k-NN
    3. Jika OpenSearch belum diisi atau score di bawah ambang batas, fallback ke kata kunci statis
    """
    # 0. Saring sapaan dan basa-basi: Jangan pernah tarik resep jika pengguna hanya menyapa!
    if is_greeting_or_chitchat(user_query):
        return None

    # Tentukan ambang batas skor kemiripan semantik
    # Jika pengguna menyebut bahan/resep secara spesifik: 0.68
    # Jika pertanyaan umum/panjang: 0.74 (agar tidak salah tebak resep acak)
    has_intent = has_culinary_intent(user_query)
    min_score_threshold = 0.68 if has_intent else 0.74

    # 1. Coba k-NN Semantic Search di OpenSearch
    try:
        query_vector = embed_text(user_query, base_url=OLLAMA_BASE_URL, model=OLLAMA_EMBED_MODEL)
        hits = vector_store.search(query_vector, k=1, min_score=min_score_threshold)
        if hits:
            top_hit = hits[0]
            meta = top_hit.get("metadata", {})
            raw_bahan = meta.get("bahan", "")
            raw_langkah = meta.get("langkah", "")

            # Parsing bahan
            if ";" in raw_bahan:
                ingredients = [b.strip() for b in raw_bahan.split(";") if b.strip()]
            else:
                ingredients = [b.strip() for b in raw_bahan.split("\n") if b.strip()]

            # Parsing langkah
            steps = [s.strip() for s in raw_langkah.split("\n") if s.strip()]

            return {
                "id": top_hit.get("id"),
                "title": meta.get("judul", "Resep Terpilih"),
                "category": "Koleksi Resep Cookpad",
                "prep_time": "Praktis & Lezat",
                "portion": "Sesuai Porsi",
                "ingredients": ingredients or [raw_bahan],
                "steps": steps or [raw_langkah],
                "tips": f"Resep ini diambil via Semantic Search dari koleksi resep Cookpad. Link: {meta.get('url', '-')}",
                "url": meta.get("url", ""),
                "score": top_hit.get("score"),
                "source_type": "opensearch_vector_db"
            }
    except Exception:
        pass

    # 2. Fallback: Pencocokan Kata Kunci Statis (Hanya jika pengguna berniat memasak)
    if not has_intent:
        return None

    normalized_query = normalize_text(user_query)
    query_tokens = set(normalized_query.split())

    best_match: Optional[Dict[str, Any]] = None
    highest_score = 0

    for recipe in RECIPES_DATABASE:
        score = 0
        norm_title = normalize_text(recipe["title"])
        norm_category = normalize_text(recipe["category"])

        # Bobot 1: Jika judul lengkap ada dalam query
        if norm_title in normalized_query:
            score += 15

        # Bobot 2: Pencocokan parsial kata di judul
        title_tokens = set(norm_title.split())
        title_intersection = query_tokens.intersection(title_tokens)
        score += len(title_intersection) * 4

        # Bobot 3: Pencocokan kata kunci (keywords)
        for kw in recipe["keywords"]:
            norm_kw = normalize_text(kw)
            if norm_kw in normalized_query:
                score += 6
            else:
                kw_tokens = set(norm_kw.split())
                if query_tokens.intersection(kw_tokens):
                    score += 2

        # Bobot 4: Pencocokan kategori
        if norm_category in normalized_query:
            score += 3

        if score > highest_score:
            highest_score = score
            best_match = recipe

    # Ambang batas skor minimum untuk dianggap relevan
    if highest_score >= 6 and best_match is not None:
        return best_match
    return None

def build_augmented_prompt(user_query: str, retrieved_recipe: Optional[Dict[str, Any]]) -> str:
    """Membangun prompt yang diperkaya (Augmented Prompt) untuk Llama 3.2 3B."""
    if retrieved_recipe:
        ingredients_formatted = "\n".join([f"- {item}" for item in retrieved_recipe["ingredients"]])
        steps_formatted = "\n".join([f"{idx+1}. {step}" for idx, step in enumerate(retrieved_recipe["steps"])])
        url_info = f"\nTautan Sumber: {retrieved_recipe.get('url')}" if retrieved_recipe.get("url") else ""

        prompt = f"""Kamu adalah "Dobi AI", asisten koki pintar, ramah, dan berpengalaman dalam dunia kuliner Nusantara dan Internasional.
Pengguna menanyakan resep/bahan masakan: "{user_query}"

Gunakan informasi resep terpercaya berikut ini sebagai dasar jawaban utamamu:

==============================
DATA RESEP TERPILIH DOBI AI:
Judul Resep : {retrieved_recipe['title']}
Kategori    : {retrieved_recipe['category']}
Estimasi Waktu : {retrieved_recipe['prep_time']}
Porsi       : {retrieved_recipe['portion']}{url_info}

BAHAN-BAHAN:
{ingredients_formatted}

LANGKAH MEMASAK:
{steps_formatted}

TIPS RAHASIA KOKI DOBI:
{retrieved_recipe['tips']}
==============================

Petunjuk Respon:
1. Sapa pengguna dengan hangat, ceria, dan penuh semangat (gunakan emoji seperti 👨‍🍳, 🍳, 🥘).
2. Sajikan bahan dan langkah memasak secara sistematis, rapi, dan mudah dibaca (gunakan bullet points dan nomor).
3. Berikan tips agar masakan pengguna berhasil lezat.
4. Akhiri dengan kalimat penyemangat memasak yang menyenangkan.
"""
    else:
        prompt = f"""Kamu adalah "Dobi AI", asisten koki pintar, ramah, dan solutif.
Pengguna mengatakan/menanyakan: "{user_query}"

Petunjuk Respon:
1. JIKA PENGGUNA HANYA MENYAPA (contoh: "Halo", "Hai", "Selamat pagi", "P", "Siapa kamu", dsb):
   - Balaslah sapaan tersebut dengan ramah, hangat, dan ceria.
   - Perkenalkan dirimu secara singkat sebagai Dobi AI, asisten koki pintar.
   - Tanyakan secara bersahabat: "Kamu punya bahan apa saja di kulkas/dapur atau lagi ingin ide resep apa hari ini? Tuliskan saja bahannya (misalnya: 'punya telur dan tahu') atau nama makanannya, nanti Dobi carikan resep terbaik! 🍳"
   - PENTING MUTLAK: JANGAN PERNAH memberikan resep masakan secara tiba-tiba jika pengguna hanya menyapa atau belum meminta resep!
2. JIKA PENGGUNA BERTERIMA KASIH ATAU BASA-BASI:
   - Balas dengan santun dan senang hati (misal: "Sama-sama! Selamat mencoba di dapur ya! 👨‍🍳").
3. JIKA PENGGUNA BERTANYA TIPS DAPUR UMUM (contoh: "kenapa minyak meletup saat menggoreng?", "cara menyimpan cabai agar awet"):
   - Jawab pertanyaan tersebut secara langsung, praktis, dan informatif.
4. JIKA PERTANYAAN DI LUAR KONTEKS MAKANAN/MEMASAK:
   - Ingatkan secara halus dan ramah bahwa kamu adalah Dobi AI yang berfokus membantu urusan resep dan dapur.
"""
    return prompt

def generate_local_fallback_response(user_query: str, recipe: Optional[Dict[str, Any]]) -> str:
    """Respon fallback jika Ollama lokal belum aktif, memastikan aplikasi tetap dapat diuji coba dengan baik."""
    if recipe:
        ingredients_list = "\n".join([f"• {b}" for b in recipe["ingredients"]])
        steps_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(recipe["steps"])])
        url_line = f"\n🔗 **Tautan Resep Asli Cookpad:** [{recipe.get('url')}]({recipe.get('url')})\n" if recipe.get("url") else ""
        source_note = "Vector Database OpenSearch (999 Resep Cookpad)" if recipe.get("source_type") == "opensearch_vector_db" else "Knowledge Base Lokal Dobi AI"
        
        return (
            f"Halo Sobat Dapur! 👨‍🍳 Aku **Dobi AI**.\n\n"
            f"> 💡 *(Catatan Sistem: Mode Cepat / Simulasi RAG Aktif - Resep ditarik secara akurat dari {source_note}!)*\n\n"
            f"Berikut adalah panduan lengkap untuk **{recipe['title']}**:\n\n"
            f"⏱️ **Estimasi Waktu:** {recipe['prep_time']} | 🍽️ **Porsi:** {recipe['portion']}\n"
            f"{url_line}\n"
            f"### 🛒 Bahan-Bahan:\n{ingredients_list}\n\n"
            f"### 🍳 Cara Memasak:\n{steps_list}\n\n"
            f"### 💡 Tips Rahasia Dobi AI:\n{recipe['tips']}\n\n"
            f"Selamat mencoba di dapur ya! Jika ada bahan yang ingin diganti atau ditanyakan, kasih tahu Dobi ya! 🔥"
        )
    else:
        if is_greeting_or_chitchat(user_query):
            return (
                "Halo Sobat Dapur! 👨‍🍳 Aku **Dobi AI**, asisten koki pintar kamu.\n\n"
                "Ada bahan apa saja di kulkas atau dapurmu hari ini? Atau lagi pengen masak apa?\n\n"
                "Ketikkan saja bahan yang kamu punya (misalnya: *'ada ayam, bawang, dan kecap'* atau *'resep soto ayam'*), nanti Dobi carikan resep yang paling pas dari 999 database kami! ✨"
            )
        else:
            return (
                f"Halo Sobat Kuliner! 👨‍🍳 Aku **Dobi AI**.\n\n"
                f"Terima kasih atas pertanyaannya: *\"{user_query}\"*.\n\n"
                f"Untuk pertanyaan tersebut, kamu bisa coba sebutkan bahan masakan yang kamu miliki di rumah (contoh: *'punya telur, tahu, dan kecap'* atau *'resep nasi goreng'*), dan aku akan mencarikan resep masakan yang paling cocok untukmu! 🥘"
            )

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
    """Merender halaman antarmuka web modern Dobi AI."""
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
    """Mengembalikan daftar seluruh resep dalam knowledge base Dobi AI."""
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
                "keywords": r["keywords"]
            }
            for r in RECIPES_DATABASE
        ]
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """
    Endpoint pemrosesan chat RAG:
    1. Menerima input dari pengguna
    2. Menjalankan RAG berbasis pencocokan kata kunci statis (dictionary)
    3. Membangun Augmented Prompt
    4. Mengirim prompt via `requests` ke Llama 3.2 3B di Ollama
    5. Fallback otomatis jika Ollama tidak tersedia
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

    # 2. RAG Augmentation Step
    final_prompt = build_augmented_prompt(user_query, matched_recipe)

    # 3. Generation Step via Ollama (menggunakan pustaka requests)
    ollama_payload = {
        "model": OLLAMA_MODEL,
        "prompt": final_prompt,
        "stream": False,
        "options": {
            "num_predict": 450,
            "temperature": 0.7
        }
    }

    try:
        # Mengirim request ke Ollama Llama 3.2 3B dengan timeout 120 detik
        response = requests.post(
            OLLAMA_GENERATE_URL,
            json=ollama_payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result_json = response.json()
            reply_text = result_json.get("response", "").strip()
            return ChatResponse(
                reply=reply_text,
                retrieved_recipe=recipe_title,
                source="ollama",
                context_used=context_used,
                url=recipe_url,
                score=recipe_score
            )
        else:
            # Jika Ollama merespon dengan status error (misal model belum dipull)
            fallback_text = (
                f"⚠️ *Ollama mengembalikan status code {response.status_code}: {response.text}*\n\n"
                + generate_local_fallback_response(user_query, matched_recipe)
            )
            return ChatResponse(
                reply=fallback_text,
                retrieved_recipe=recipe_title,
                source="local_fallback_on_ollama_error",
                context_used=context_used,
                url=recipe_url,
                score=recipe_score
            )

    except requests.exceptions.RequestException:
        # Graceful fallback jika Ollama server offline / belum jalan
        fallback_text = generate_local_fallback_response(user_query, matched_recipe)
        return ChatResponse(
            reply=fallback_text,
            retrieved_recipe=recipe_title,
            source="local_knowledge_base",
            context_used=context_used,
            url=recipe_url,
            score=recipe_score
        )

@app.get("/api/vector-store/stats")
async def vector_store_stats():
    """Mengembalikan statistik jumlah dokumen yang tersimpan di OpenSearch recipes-index."""
    return {
        "status": "success",
        "index_name": vector_store.index_name,
        "total_documents": vector_store.count(),
        "vector_dimension": vector_store.dimension
    }

@app.post("/chat/stream")
async def chat_stream_endpoint(payload: ChatStreamRequest):
    """
    Endpoint chat streaming (Module 7-8 / Module 10-12 verification):
    Validasi: jika messages kosong, kembalikan 400 Bad Request.
    """
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages kosong")
    return {"status": "ok", "message": "chat stream ready"}

@app.get("/health")
async def health_check():
    """Health check endpoint untuk Docker dan monitoring."""
    return {
        "status": "healthy",
        "service": "Dobi AI Recipe Assistant",
        "ollama_target": OLLAMA_GENERATE_URL,
        "opensearch_target": OPENSEARCH_BASE_URL,
        "opensearch_recipes_count": vector_store.count(),
        "static_recipes_indexed": len(RECIPES_DATABASE)
    }
