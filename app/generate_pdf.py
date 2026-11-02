import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
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
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header garis tipis
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(40, 800, 555, 800)
        self.drawString(40, 805, "Dobi AI — Panduan Setup & Update Proyek untuk Rekan Kolaborasi")

        # Footer
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, "Dokumen Teknis Tim Pengembang • Branch: main • Fast RAG Recipe Assistant")
        self.drawRightString(555, 32, f"Halaman {self._pageNumber} dari {page_count}")
        self.restoreState()

def create_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=55,
        bottomMargin=55
    )

    styles = getSampleStyleSheet()

    # Warna Tema Dobi
    c_primary = colors.HexColor("#ea580c")    # Orange Dobi
    c_dark = colors.HexColor("#0f172a")       # Slate gelap
    c_body = colors.HexColor("#334155")       # Teks normal
    c_code_bg = colors.HexColor("#f8fafc")    # Background abu-abu kode
    c_box_border = colors.HexColor("#cbd5e1") # Border box
    c_badge_bg = colors.HexColor("#ffedd5")   # Orange muda badge

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_dark,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=c_primary,
        spaceAfter=15
    )

    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=c_dark,
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=c_body,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0f172a")
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=body_style,
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#9a3412")
    )

    def make_code_box(command_str: str):
        content = [Paragraph(command_str.replace('\n', '<br/>'), code_style)]
        t = Table([[content]], colWidths=[515])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), c_code_bg),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ]))
        return t

    def make_note_box(note_str: str, title: str = "Catatan Penting"):
        text = f"<b>{title}:</b> {note_str}"
        p = Paragraph(text, callout_style)
        t = Table([[p]], colWidths=[515])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fff7ed")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fdba74")),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        return t

    elements = []

    # Judul & Subtitle
    elements.append(Spacer(1, 5))
    elements.append(Paragraph("Panduan Menjalankan & Memperbarui Dobi AI", title_style))
    elements.append(Paragraph("Untuk Rekan Tim / Kolaborator yang Sudah Pernah Clone Repositori Sebelumnya", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=0, spaceAfter=12))

    # Ringkasan Skenario
    elements.append(Paragraph(
        "Panduan ini dirancang khusus untuk rekan yang <b>sudah memiliki salinan repositori lokal (clone sebelumnya)</b> "
        "dan <b>kemungkinan sudah memiliki Ollama di Docker</b>. Ikuti 5 langkah ringkas berikut untuk menyinkronkan "
        "seluruh fitur terbaru (Vector DB OpenSearch 999 resep, arsitektur knowledge-base modular, dan UI responsif).",
        body_style
    ))
    elements.append(Spacer(1, 4))

    # Langkah 1
    elements.append(Paragraph("Langkah 1: Masuk ke Folder Proyek & Tarik Pembaruan (Git Pull)", h2_style))
    elements.append(Paragraph(
        "Buka terminal (PowerShell, Command Prompt, atau Git Bash), navigasikan ke folder repositori yang sudah pernah di-clone, "
        "kemudian lakukan pull dari branch <b>main</b>:",
        body_style
    ))
    elements.append(make_code_box(
        "# Masuk ke folder proyek yang sudah pernah di-clone sebelumnya\n"
        "cd dobi-ai\n\n"
        "# Tarik seluruh pembaruan commit terbaru\n"
        "git pull origin main"
    ))
    elements.append(Spacer(1, 4))
    elements.append(make_note_box(
        "Jika ada error konflik karena perubahan lokal yang belum di-commit, jalankan <code>git stash</code> terlebih dahulu sebelum <code>git pull</code>.",
        title="Tips Jika Ada Konflik"
    ))
    elements.append(Spacer(1, 8))

    # Langkah 2
    elements.append(Paragraph("Langkah 2: Bangun Ulang & Jalankan Kontainer Docker", h2_style))
    elements.append(Paragraph(
        "Pembaruan terbaru menyertakan service baru (<b>OpenSearch Vector DB</b>, <b>OpenSearch Dashboards</b>, dan <b>Cloudflare Tunnel</b>). "
        "Nyalakan seluruh service dengan perintah build:",
        body_style
    ))
    elements.append(make_code_box(
        "# Build ulang dan jalankan seluruh container di background\n"
        "docker compose up -d --build"
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Tunggu hingga seluruh container berstatus <b>Started</b> (<i>api</i>, <i>ollama</i>, <i>opensearch</i>, <i>opensearch-dashboards</i>, <i>dobi-ai-tunnel</i>).",
        body_style
    ))
    elements.append(Spacer(1, 8))

    # Langkah 3
    elements.append(Paragraph("Langkah 3: Verifikasi Model AI di Ollama (Hanya Cek & Pull jika Kurang)", h2_style))
    elements.append(Paragraph(
        "Karena di laptop rekan Anda kemungkinan sudah ada Ollama, <b>tidak perlu setup ulang Ollama</b>. Cukup cek apakah "
        "kedua model yang dibutuhkan sudah terdaftar:",
        body_style
    ))
    elements.append(make_code_box("docker compose exec ollama ollama list"))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Pastikan kedua model berikut muncul di daftar:<br/>"
        "• <b>llama3.2:3b</b> (Model utama pembuat jawaban & percakapan)<br/>"
        "• <b>nomic-embed-text</b> (Model vektor embedding 768 dimensi untuk RAG)",
        bullet_style
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Jika model <b>nomic-embed-text</b> belum ada (karena baru ditambahkan di Modul 11), jalankan:",
        body_style
    ))
    elements.append(make_code_box("docker compose exec ollama ollama pull nomic-embed-text"))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "<i>(Opsional: Jika llama3.2:3b belum terpasang, jalankan juga: <code>docker compose exec ollama ollama pull llama3.2:3b</code>)</i>",
        body_style
    ))
    elements.append(Spacer(1, 8))

    # Langkah 4
    elements.append(Paragraph("Langkah 4: Masukkan 999 Resep ke Vector DB OpenSearch (Ingestion)", h2_style))
    elements.append(Paragraph(
        "Karena kontainer OpenSearch baru saja dijalankan di laptop rekan, indeks vektor resep perlu diisi dari file dataset Cookpad yang sudah ada:",
        body_style
    ))
    elements.append(make_code_box(
        "# Jalankan skrip ingestion dataset resep ke OpenSearch\n"
        "docker compose exec api python -m app.ingest_csv"
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Tunggu sekitar 1–2 menit sampai proses 100% selesai dan muncul notifikasi sukses: "
        "<b>'🎉 SELESAI! 999 dari 999 resep berhasil tersimpan di OpenSearch.'</b>",
        body_style
    ))
    elements.append(Spacer(1, 8))

    # Langkah 5
    elements.append(Paragraph("Langkah 5: Buka Aplikasi & Lakukan Pengujian", h2_style))
    elements.append(Paragraph("Buka web browser dan akses tautan lokal berikut:", body_style))

    table_data = [
        [Paragraph("<b>Layanan</b>", body_style), Paragraph("<b>Tautan URL</b>", body_style), Paragraph("<b>Deskripsi</b>", body_style)],
        [Paragraph("Aplikasi Web Dobi AI", body_style), Paragraph("<b>http://localhost:8000</b>", code_style), Paragraph("Antarmuka chat asisten koki resep pintar", body_style)],
        [Paragraph("OpenSearch Dashboards", body_style), Paragraph("<b>http://localhost:5601</b>", code_style), Paragraph("Visual UI database indeks vektor resep", body_style)],
        [Paragraph("Status Health API", body_style), Paragraph("<b>http://localhost:8000/health</b>", code_style), Paragraph("Cek status koneksi model & total resep terindeks", body_style)]
    ]
    tb = Table(table_data, colWidths=[135, 175, 205])
    tb.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(tb)
    elements.append(Spacer(1, 10))

    # Langkah 6 (Tunneling)
    elements.append(Paragraph("Langkah Tambahan: Membuka Website di HP (Cloudflare Tunnel)", h2_style))
    elements.append(Paragraph(
        "Jika rekan Anda ingin mencoba membuka aplikasi dari HP atau membagikannya ke teman lain tanpa konfigurasi port-forwarding, "
        "cukup cek log tunnel otomatis yang sedang berjalan:",
        body_style
    ))
    elements.append(make_code_box(
        "# Cek tautan publik Cloudflare yang di-generate otomatis\n"
        "docker compose logs tunnel"
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Cari baris yang mencantumkan URL seperti: <code>https://xxxx-xxxx-xxxx.trycloudflare.com</code>. "
        "Tautan tersebut aman, ber-HTTPS, dan bisa dibuka langsung di browser smartphone selama laptop tetap menyala.",
        body_style
    ))
    elements.append(Spacer(1, 10))

    # Ringkasan Perintah Sehari-hari
    elements.append(Paragraph("Perintah Rutin untuk Bekerja Sehari-hari", h2_style))
    elements.append(Paragraph(
        "• <b>Mematikan service:</b> <code>docker compose down</code><br/>"
        "• <b>Menjalankan kembali:</b> <code>docker compose up -d</code> <i>(Data 999 resep dan model AI tetap tersimpan di volume, tidak perlu diunduh ulang)</i><br/>"
        "• <b>Melihat log backend:</b> <code>docker compose logs -f api</code>",
        bullet_style
    ))

    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"PDF berhasil dibuat di: {output_path}")

if __name__ == "__main__":
    out_file = "/app/app/PANDUAN_SETUP_DOBI_AI.pdf"
    create_pdf(out_file)
