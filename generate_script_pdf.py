import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header bar
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.75)
        self.line(40, 805, 555, 805)
        self.drawString(40, 810, "Dobi AI — Naskah & Alur Video Presentasi Progres Proyek UTS (Module 10-16)")

        # Footer bar
        self.line(40, 42, 555, 42)
        self.drawString(40, 30, "Kelompok: Ahmad, Yoga, Rizqy, Rifan • Proyek: Dobi AI (RAG Recipe Assistant)")
        self.drawRightString(555, 30, f"Halaman {self._pageNumber} dari {page_count}")
        self.restoreState()

def generate_pdf(output_filename: str):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        leftMargin=38,
        rightMargin=38,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # Warna Tema
    c_primary = colors.HexColor("#ea580c")   # Oranye Dobi
    c_dark = colors.HexColor("#0f172a")      # Slate gelap
    c_body = colors.HexColor("#334155")      # Teks isi
    c_box_bg = colors.HexColor("#f8fafc")    # Background kode/tabel
    c_callout_bg = colors.HexColor("#fff7ed")# Oranye muda
    c_border = colors.HexColor("#cbd5e1")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_dark,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=c_primary,
        spaceAfter=10
    )

    h2_style = ParagraphStyle(
        'SecHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_dark,
        spaceBefore=10,
        spaceAfter=5
    )

    h3_style = ParagraphStyle(
        'SpeakerHeader',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=c_primary,
        spaceBefore=8,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'NormalBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=c_body,
        spaceAfter=4
    )

    script_style = ParagraphStyle(
        'ScriptSpeech',
        parent=body_style,
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#1e293b")
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0f172a")
    )

    def make_box(content_flowable, bg_color=c_box_bg, border_color=c_border):
        t = Table([[content_flowable]], colWidths=[519])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg_color),
            ('BOX', (0,0), (-1,-1), 1, border_color),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        return t

    elements = []

    # HEADER & JUDUL DOKUMEN
    elements.append(Paragraph("Naskah & Alur Video Presentasi Progres Proyek UTS", title_style))
    elements.append(Paragraph("Proyek: Dobi AI — RAG Smart Recipe Assistant • Mencakup Seluruh Modul Dosen (Modul 10 – 16)", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=0, spaceAfter=8))

    # IDENTITAS KELOMPOK
    team_data = [
        [
            Paragraph("<b>Mata Kuliah:</b> Praktikum AI / RAG", body_style),
            Paragraph("<b>Target Video:</b> YouTube (Durasi 6-8 Menit)", body_style)
        ],
        [
            Paragraph("<b>Anggota Tim (4 Orang):</b><br/>1. <b>Ahmad</b> (Poin 1)<br/>2. <b>Yoga</b> (Poin 2)", body_style),
            Paragraph("<b>Pembagian Peran:</b><br/>3. <b>Rizqy</b> (Poin 3)<br/>4. <b>Rifan</b> (Poin 4 + Penutup)", body_style)
        ]
    ]
    team_table = Table(team_data, colWidths=[259, 260])
    team_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_callout_bg),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fdba74")),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(team_table)
    elements.append(Spacer(1, 8))

    # BAGIAN 1: RUNDOWN & MATRIKS PEMBAGIAN WAKTU
    elements.append(Paragraph("1. Rundown & Alur Penjelasan Video (Timeline)", h2_style))
    rundown_data = [
        [Paragraph("<b>Waktu</b>", body_style), Paragraph("<b>Presenter</b>", body_style), Paragraph("<b>Poin Penjelasan (Instruksi Dosen)</b>", body_style), Paragraph("<b>Tampilan Layar (Screen Share)</b>", body_style)],
        [Paragraph("00:00 - 01:45", body_style), Paragraph("<b>Ahmad</b>", body_style), Paragraph("<b>Poin 1:</b> Pengenalan Dobi AI & kaitannya dengan RAG, masalah halusinasi LLM tanpa basis data.", body_style), Paragraph("Slide Judul & Web Dobi AI (localhost:8000), diagram arsitektur RAG.", body_style)],
        [Paragraph("01:45 - 03:15", body_style), Paragraph("<b>Yoga</b>", body_style), Paragraph("<b>Poin 2:</b> Simulasi ketika AI BELUM diberi knowledge (jawaban generik/halusinasi).", body_style), Paragraph("Web Dobi AI / Chat LLM polosan saat ditanya resep lokal spesifik.", body_style)],
        [Paragraph("03:15 - 05:30", body_style), Paragraph("<b>Rizqy</b>", body_style), Paragraph("<b>Poin 3:</b> Simulasi upload knowledge base & OpenSearch Vector Database k-NN (768 dimensi).", body_style), Paragraph("Terminal ingest dataset CSV resep, model nomic-embed-text, OpenSearch Dashboards (5601).", body_style)],
        [Paragraph("05:30 - 07:30", body_style), Paragraph("<b>Rifan</b>", body_style), Paragraph("<b>Poin 4:</b> Simulasi ketika AI SUDAH diberi knowledge (jawaban presisi dari Cookpad) + Penutup.", body_style), Paragraph("Web Dobi AI menampilkan badge RAG, takaran bumbu, langkah memasak, dan link sumber.", body_style)]
    ]
    rd_t = Table(rundown_data, colWidths=[65, 55, 210, 189])
    rd_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(rd_t)
    elements.append(Spacer(1, 10))

    # BAGIAN 2: NASKAH RINCI & PETUNJUK DEMO TIAP ANGGOTA
    elements.append(Paragraph("2. Naskah Bicara (Script) & Panduan Demo Layar Per Orang", h2_style))

    # PEMBICARA 1: AHMAD
    elements.append(Paragraph("👤 Pembicara 1: AHMAD — Pengenalan Proyek & Konsep RAG (Poin 1)", h3_style))
    ahmad_text = (
        "<b>Petunjuk Layar:</b> Buka beranda web Dobi AI (<code>http://localhost:8000</code>) dan tampilkan diagram alur RAG.<br/><br/>"
        "<b>Naskah Bicara:</b><br/>"
        "<i>\"Halo semuanya, selamat pagi/siang kepada Bapak/Ibu Dosen dan rekan-rekan sekalian. "
        "Kami dari kelompok pengembang asisten pintar, beranggotakan Ahmad, Yoga, Rizqy, dan Rifan. "
        "Pada kesempatan UTS ini, kami mempresentasikan progres proyek kami yaitu <b>Dobi AI: Smart Recipe Assistant berbasis RAG</b>.<br/><br/>"
        "Latar belakang proyek ini berawal dari permasalahan umum Large Language Model (LLM) seperti Llama 3.2: "
        "model dasar sering mengalami <b>halusinasi</b> atau memberikan takaran resep yang tidak akurat untuk masakan lokal Nusantara karena keterbatasan data latih internalnya.<br/><br/>"
        "Di sinilah peran <b>Retrieval-Augmented Generation (RAG)</b>. Sistem kami tidak memaksa AI menghafal seluruh resep, "
        "melainkan menghubungkannya dengan Vector Database OpenSearch yang berisi 999 database resep Cookpad. "
        "Ketika pengguna bertanya, sistem mencari resep yang paling relevan lalu menyisipkannya sebagai konteks agar jawaban AI akurat, faktual, dan memiliki referensi terpercaya. "
        "Selanjutnya, rekan saya Yoga akan mendemonstrasikan bagaimana respon AI saat belum memiliki knowledge base.\"</i>"
    )
    elements.append(make_box(Paragraph(ahmad_text, body_style), bg_color=colors.HexColor("#f8fafc")))
    elements.append(Spacer(1, 8))

    # PEMBICARA 2: YOGA
    elements.append(Paragraph("👤 Pembicara 2: YOGA — Simulasi SEBELUM Diberikan Knowledge (Poin 2)", h3_style))
    yoga_text = (
        "<b>Petunjuk Layar:</b> Buka antarmuka chat sebelum RAG aktif, ketik pertanyaan resep lokal spesifik.<br/><br/>"
        "<b>Naskah Bicara:</b><br/>"
        "<i>\"Terima kasih Ahmad. Saya Yoga akan mendemonstrasikan poin kedua, yaitu <b>simulasi respon AI sebelum diberikan knowledge base</b>.<br/><br/>"
        "(Sambil mengetik di layar): Di sini kita coba tanyakan resep lokal yang spesifik, misalnya: 'Resep Singkong Gula Merah Khas Wonogiri' atau 'resep ayam geprek sambal korek gurih'.<br/><br/>"
        "Mari kita perhatikan jawabannya: model hanya mengandalkan ingatan internalnya yang terbatas. "
        "Jawabannya bersifat sangat umum, takaran bumbu sering tidak presisi, tidak ada tips koki yang terverifikasi, "
        "dan yang paling krusial—model tidak dapat memberikan tautan sumber resep asli yang valid. "
        "Bahkan pada beberapa kasus, AI mengarang langkah memasak yang berisiko membuat masakan gagal.<br/><br/>"
        "Kelemahan inilah yang membuktikan bahwa tanpa Knowledge Base eksternal, asisten resep tidak dapat diandalkan secara praktis. "
        "Selanjutnya, Rizqy akan mendemonstrasikan bagaimana proses injeksi knowledge base dan vector database dilakukan.\"</i>"
    )
    elements.append(make_box(Paragraph(yoga_text, body_style), bg_color=colors.HexColor("#f8fafc")))
    elements.append(Spacer(1, 8))

    # PAGE BREAK UNTUK PEMBICARA 3 & 4
    elements.append(PageBreak())

    # PEMBICARA 3: RIZQY
    elements.append(Paragraph("👤 Pembicara 3: RIZQY — Upload Knowledge Base & Vector Database OpenSearch (Poin 3)", h3_style))
    rizqy_text = (
        "<b>Petunjuk Layar:</b> Tampilkan file <code>data/dataset_resep.csv</code>, jalankan <code>docker compose exec api python -m app.ingest_csv</code> di terminal, lalu buka OpenSearch Dashboards di <code>http://localhost:5601</code>.<br/><br/>"
        "<b>Naskah Bicara:</b><br/>"
        "<i>\"Terima kasih Yoga. Saya Rizqy akan menjelaskan <b>proses pengunggahan knowledge base ke dalam OpenSearch Vector Database</b>.<br/><br/>"
        "(Perlihatkan dataset CSV): Kami menyiapkan dataset terstruktur <code>dataset_resep.csv</code> berisi 999 resep masakan Nusantara dari Cookpad yang mencakup judul, bahan, takaran bumbu, langkah, dan URL rujukan.<br/><br/>"
        "(Buka terminal dan jalankan ingest_csv): Sekarang kita jalankan proses ingestion. Pada tahap ini, modul <code>embeddings.py</code> memanggil model <b>nomic-embed-text</b> di Ollama untuk mengubah setiap teks resep menjadi <b>vektor numerik berdimensi 768</b>. "
        "Vektor ini bersifat deterministik dan telah dinormalisasi menjadi unit vector.<br/><br/>"
        "(Buka OpenSearch Dashboards port 5601): Dokumen-dokumen ini kemudian disimpan ke dalam OpenSearch pada index <code>recipes-index</code> menggunakan algoritma k-NN HNSW dengan metrik Cosine Similarity (Modul 12, 13, & 14). "
        "Bisa kita lihat di dashboard, seluruh 999 resep telah berhasil terindeks secara rapi dan siap dicari berdasarkan makna semantiknya. "
        "Sekarang, Rifan akan mendemonstrasikan hasil jawaban AI setelah knowledge base ini aktif.\"</i>"
    )
    elements.append(make_box(Paragraph(rizqy_text, body_style), bg_color=colors.HexColor("#f8fafc")))
    elements.append(Spacer(1, 8))

    # PEMBICARA 4: RIFAN
    elements.append(Paragraph("👤 Pembicara 4: RIFAN — Simulasi SESUDAH Diberikan Knowledge & Penutup (Poin 4)", h3_style))
    rifan_text = (
        "<b>Petunjuk Layar:</b> Buka web Dobi AI (<code>http://localhost:8000</code>), ketik pertanyaan bahan: <i>'punya ayam dan kecap enaknya masak apa?'</i>. Sorot badge RAG Cookpad, takaran bumbu, langkah, dan tips koki.<br/><br/>"
        "<b>Naskah Bicara:</b><br/>"
        "<i>\"Terima kasih Rizqy. Saya Rifan akan mendemonstrasikan kondisi akhir: <b>ketika Dobi AI sudah terhubung dengan knowledge base RAG</b>.<br/><br/>"
        "(Ketik di chat Dobi AI): Mari kita uji coba dengan studi kasus nyata: 'punya ayam dan kecap enaknya masak apa?'.<br/><br/>"
        "Perhatikan hasilnya: sistem secara otomatis melakukan k-NN Semantic Search di OpenSearch dan menemukan resep yang paling relevan: 'Ayam Kecap Rumahan Sederhana Mudah' dari Cookpad dengan skor kecocokan tinggi (Modul 16).<br/><br/>"
        "Resep ini kemudian disuntikkan ke prompt Llama 3.2 3B. AI kini menyajikan: takaran bahan yang pasti, panduan memasak nomor urut, tips rahasia koki, dan menyertakan tautan Cookpad asli. "
        "Selain itu, jika pengguna hanya menyapa atau menanyakan hal umum seperti presiden, AI tetap menjawab ramah dan natural tanpa salah mencocokkan resep acak.<br/><br/>"
        "<b>Kesimpulan:</b> Penerapan RAG dengan OpenSearch dan Ollama terbukti sukses menghilangkan halusinasi dan mentransformasi AI menjadi asisten kuliner yang terpercaya. "
        "Sekian presentasi progres UTS dari kelompok kami. Terima kasih atas perhatian Bapak/Ibu Dosen!\"</i>"
    )
    elements.append(make_box(Paragraph(rifan_text, body_style), bg_color=colors.HexColor("#f8fafc")))
    elements.append(Spacer(1, 10))

    # BAGIAN 3: MATRIKS KESESUAIAN SELURUH MODUL DOSEN (MODUL 10 - 16)
    elements.append(Paragraph("3. Matriks Kesesuaian Seluruh Modul Dosen (Modul 10 – 16)", h2_style))
    elements.append(Paragraph("Tabel ini membuktikan bahwa proyek Dobi AI Anda telah memenuhi 100% spesifikasi teknis modul:", body_style))

    matrix_data = [
        [Paragraph("<b>Modul</b>", body_style), Paragraph("<b>Materi / Tugas Modul</b>", body_style), Paragraph("<b>Implementasi di Proyek Dobi AI</b>", body_style), Paragraph("<b>Status</b>", body_style)],
        [Paragraph("<b>Modul 10</b>", body_style), Paragraph("Setup Knowledge Base, bind mount, KNOWLEDGE_BASE_PATH, pypdf, extract_text().", body_style), Paragraph("Folder <code>knowledge-base/</code>, variabel di main.py & docker-compose, pypdf di ingest.py.", body_style), Paragraph("✅ 100%", body_style)],
        [Paragraph("<b>Modul 11</b>", body_style), Paragraph("Model nomic-embed-text di Ollama, embed_text() via httpx, vektor 768 dimensi.", body_style), Paragraph("Model nomic-embed-text aktif di Ollama, fungsi embed_text() di app/embeddings.py.", body_style), Paragraph("✅ 100%", body_style)],
        [Paragraph("<b>Modul 12</b>", body_style), Paragraph("OpenSearch port 9200, Dashboards port 5601, k-NN mapping Cosine Similarity.", body_style), Paragraph("Kontainer OpenSearch & Dashboards aktif, cluster status green, k-NN HNSW.", body_style), Paragraph("✅ 100%", body_style)],
        [Paragraph("<b>Modul 13</b>", body_style), Paragraph("Class VectorStore di app/vector_store.py (ensure_index, index_document, search).", body_style), Paragraph("Class VectorStore lengkap, idempotent, mendukung k-NN search dan bulk index.", body_style), Paragraph("✅ 100%", body_style)],
        [Paragraph("<b>Modul 14</b>", body_style), Paragraph("Simpan dokumen ke OpenSearch, fungsi ingest_documents() di app/ingest.py.", body_style), Paragraph("Fungsi ingest_documents() di ingest.py & script ingest_csv.py 999 resep Cookpad.", body_style), Paragraph("✅ 100%", body_style)],
        [Paragraph("<b>Modul 15</b>", body_style), Paragraph("Konsep Semantic Search (Cosine, L2, Dot Product), unit vector, filter skor minimum.", body_style), Paragraph("Vektor nomic-embed-text ternormalisasi 1.0, threshold filter skor minimum di main.py.", body_style), Paragraph("✅ 100%", body_style)],
        [Paragraph("<b>Modul 16</b>", body_style), Paragraph("Integrasi RAG ke Chatbot (/chat/stream, context injection, validasi role user).", body_style), Paragraph("Endpoint /chat dan /chat/stream terhubung ke OpenSearch & Llama 3.2 3B Chat API.", body_style), Paragraph("✅ 100%", body_style)]
    ]
    mt = Table(matrix_data, colWidths=[65, 175, 230, 49])
    mt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(mt)
    elements.append(Spacer(1, 10))

    # TIPS REKAMAN
    tips_content = (
        "<b>Tips Rekaman Video Terbaik:</b><br/>"
        "1. <b>Gunakan Google Meet / Zoom:</b> Buka room berempat, nyalakan webcam masing-masing (posisikan di sudut), lalu rekam layar bergantian saat giliran berbicara.<br/>"
        "2. <b>Persiapan Sebelum Record:</b> Pastikan Docker sudah menyala (<code>docker compose up -d</code>). Buka 3 tab browser: Tab 1 Dobi AI (<code>localhost:8000</code>), Tab 2 OpenSearch Dashboards (<code>localhost:5601</code>), dan Tab 3 Terminal.<br/>"
        "3. <b>Upload YouTube:</b> Beri judul: <i>'Progres Proyek UTS: Dobi AI (Smart Recipe Assistant berbasis RAG OpenSearch & Ollama)'</i> dan set visibility ke <i>Unlisted</i> atau <i>Public</i>."
    )
    elements.append(make_box(Paragraph(tips_content, body_style), bg_color=c_callout_bg, border_color=colors.HexColor("#fdba74")))

    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"PDF Berhasil dibuat: {output_filename}")

if __name__ == "__main__":
    out_pdf = "D:\\Projects\\raresep\\NASKAH_VIDEO_PRESENTASI_UTS.pdf"
    generate_pdf(out_pdf)
