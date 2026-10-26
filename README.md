# 🍳 Dobi AI - RAG Smart Recipe Assistant

**Dobi AI** adalah asisten koki pintar berbasis AI yang dirancang untuk membantu pengguna menemukan resep masakan lezat, takaran bahan, tips koki terpercaya, dan ide kuliner harian. Proyek ini mengimplementasikan konsep **Retrieval-Augmented Generation (RAG)** sederhana berbasis pencocokan kata kunci (keyword matching) yang digabungkan dengan Large Language Model **Llama 3.2 3B** melalui Ollama.

---

## 🌟 Fitur Utama

- 🎨 **Modern & Responsive UI**: Antarmuka chatbot interaktif dengan palet warna **Oranye Cerah khas kuliner**, sidebar menu di sisi kiri (daftar resep & riwayat obrolan fiktif), dan area percakapan di kanan.
- 🔍 **RAG Sederhana (Keyword Matching)**: Mengindeks basis data resep terstruktur dan mencocokkan query pengguna dengan bobot kata kunci relevan sebelum diteruskan ke LLM.
- 🤖 **Integrasi Llama 3.2 3B via Ollama**: Menghubungkan prompt yang diperkaya (*Augmented Prompt*) ke Ollama endpoint (`http://localhost:11434/api/generate`) menggunakan pustaka `requests`.
- 🛡️ **Graceful Fallback Mode**: Jika server Ollama belum aktif, Dobi AI tetap menyajikan resep dari basis data lokal secara otomatis tanpa crash!
- 🐳 **Docker & Docker Compose Ready**: Seluruh aplikasi siap dijalankan hanya dengan satu perintah `docker-compose up`.

---

## 📁 Struktur Direktori

```plaintext
d:\Projects\raresep/
├── app/
│   ├── main.py              # Backend FastAPI (RAG logic, endpoints /chat, Ollama integration)
│   └── templates/
│       └── index.html       # Frontend UI Chatbot (Tailwind CSS, sidebar, orange theme)
├── Dockerfile               # Konfigurasi container Docker berbasis Python 3.11-slim
├── docker-compose.yml       # Konfigurasi orkestrasi Docker Compose
├── requirements.txt         # Daftar dependensi Python
└── README.md                # Dokumentasi proyek
```

---

## 🧠 Cara Kerja RAG Sederhana Dobi AI

```
[Pengguna Bertanya: "Resep nasi goreng enak"]
                     │
                     ▼
       ┌───────────────────────────┐
       │ 1. Keyword Matching (RAG) │  (Mencocokkan query dengan
       │    Knowledge Base Resep   │   judul, bahan, & kata kunci)
       └─────────────┬─────────────┘
                     │ (Ditemukan: Resep Nasi Goreng Solaria)
                     ▼
       ┌───────────────────────────┐
       │ 2. Prompt Augmentation    │  (Suntikkan bahan, takaran,
       │    (Sistem Prompt Dobi)   │   dan tips ke template prompt)
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │ 3. LLM Generation         │
       │    (Llama 3.2 3B Ollama)  │  (Menggunakan requests.post
       └─────────────┬─────────────┘   ke http://localhost:11434)
                     │
                     ▼
[Jawaban Lengkap, Akurat & Ramah dari Dobi AI]
```

---

## 🚀 Panduan Menjalankan Proyek

### Cara 1: Menggunakan Docker Compose (Direkomendasikan)

Pastikan Docker Desktop sudah terpasang dan berjalan di komputer Anda.

1. Jalankan perintah berikut di root direktori proyek:
   ```bash
   docker-compose up --build
   ```

2. Buka browser dan akses antarmuka Dobi AI di:
   ```
   http://localhost:8000
   ```

3. Untuk menghentikan container:
   ```bash
   docker-compose down
   ```

---

### Cara 2: Menjalankan Secara Lokal (Python Virtual Environment)

Jika ingin menjalankan tanpa Docker:

1. Buat dan aktifkan virtual environment:
   ```bash
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   
   # Linux/macOS:
   source venv/bin/activate
   ```

2. Pasang seluruh dependensi:
   ```bash
   pip install -r requirements.txt
   ```

3. Jalankan server FastAPI:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. Buka `http://localhost:8000` pada peramban Anda.

---

## 🦙 Menghubungkan ke Model Llama 3.2 3B di Ollama

Aplikasi dikonfigurasi untuk terhubung ke model **Llama 3.2 3B**. Ikuti langkah berikut untuk mengaktifkannya di Ollama:

1. Unduh dan jalankan model Llama 3.2 3B di komputer Anda:
   ```bash
   ollama pull llama3.2:3b
   ollama run llama3.2:3b
   ```

2. Pastikan Ollama aktif di latar belakang (secara default berjalan di port `11434`).
   - Pada `docker-compose.yml`, host gateway `host.docker.internal` sudah dikonfigurasi secara otomatis agar container Docker dapat mengakses service Ollama di mesin host Anda.

> 💡 **Catatan Penting**: Jika Ollama belum Anda jalankan, Dobi AI tidak akan mengalami error atau crash. Sistem otomatis beralih ke **Mode Cepat / Local Knowledge Base Fallback** sehingga antarmuka dan RAG tetap dapat diuji secara instan!

---

## 📡 Endpoint API

| Method | Endpoint | Deskripsi |
| :--- | :--- | :--- |
| `GET` | `/` | Merender antarmuka web modern Dobi AI (`index.html`) |
| `POST` | `/chat` | Menerima pesan pengguna, memproses RAG, dan mengembalikan respon AI |
| `GET` | `/api/recipes` | Mendapatkan daftar seluruh resep yang terindeks dalam Knowledge Base |
| `GET` | `/health` | Memeriksa status kesehatan server dan konektivitas RAG |

### Contoh Request `/chat`:
```json
POST /chat
Content-Type: application/json

{
  "message": "Bagaimana cara membuat Ayam Geprek Crispy sambal bawang?"
}
```

### Contoh Response:
```json
{
  "reply": "Halo Sobat Dapur! 👨‍🍳 Aku Dobi AI. Ini dia resep Ayam Geprek Crispy Sambal Bawang...",
  "retrieved_recipe": "Ayam Geprek Crispy Sambal Bawang Pedas Nampol",
  "source": "ollama",
  "context_used": true
}
```

---

## 🎨 Tampilan Antarmuka (UI Preview)

- **Aksen Oranye Cerah (Bright Orange)** pada header, tombol kirim, badge RAG, dan efek hover.
- **Sidebar Kiri**:
  - Logo khas Dobi AI dengan ikon chef hat.
  - Tombol **Mulai Obrolan Baru**.
  - **Menu RAG Dobi AI**: Daftar menu interaktif yang dapat diklik langsung untuk memicu prompt resep.
  - **Riwayat Obrolan Fiktif**: Riwayat obrolan kuliner sebelumnya.
- **Area Chat Kanan**:
  - Header dengan avatar koki dan status online.
  - Banner sambutan dengan saran prompt cepat (*quick chips*).
  - Indikator RAG terhubung pada setiap jawaban resep.
  - Indikator mengetik (*typing animation*).
  - Input bar modern dengan integrasi keyboard (Enter / Shift+Enter).
