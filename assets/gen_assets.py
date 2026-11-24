# Sinh các file dữ liệu nhị phân mẫu cho lab (ảnh/PDF/audio).
# Chạy: uv run --with pillow --with reportlab python gen_assets.py <assets_dir>
import os, sys, math, wave, struct
from PIL import Image, ImageDraw, ImageFont

ASSETS = sys.argv[1]
os.makedirs(ASSETS, exist_ok=True)
os.makedirs(os.path.join(ASSETS, "output"), exist_ok=True)


def font(size):
    # Font hệ thống để chữ đủ lớn cho OCR; fallback nếu thiếu.
    for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def scene(path):
    # Ảnh ngoài trời: trời, nắng, bãi cỏ, ngôi nhà, cây + chữ -> captions/tags/objects/OCR đều có kết quả.
    w, h = 1024, 768
    img = Image.new("RGB", (w, h), (135, 206, 235))      # bầu trời xanh
    d = ImageDraw.Draw(img)
    d.rectangle([0, 560, w, h], fill=(96, 170, 70))       # bãi cỏ
    d.ellipse([820, 40, 960, 180], fill=(255, 214, 60))   # mặt trời
    # Ngôi nhà
    d.rectangle([360, 360, 620, 560], fill=(214, 120, 90))
    d.polygon([(340, 360), (490, 250), (640, 360)], fill=(150, 60, 50))  # mái
    d.rectangle([440, 460, 520, 560], fill=(90, 60, 40))  # cửa
    d.rectangle([390, 400, 440, 450], fill=(170, 220, 255))  # cửa sổ
    # Cây
    d.rectangle([180, 440, 210, 560], fill=(110, 70, 40))
    d.ellipse([120, 360, 270, 470], fill=(60, 140, 60))
    d.text((40, 40), "XuanDai Labs - AI-103 Demo", font=font(48), fill=(20, 20, 60))
    d.text((40, 110), "Hello Azure Vision", font=font(36), fill=(20, 20, 60))
    img.save(path, quality=90)
    return img


def mask(path, size):
    # Mask inpainting (chuẩn OpenAI images.edit): vùng TRONG SUỐT = chỗ cần vẽ lại, đục = giữ nguyên.
    w, h = size
    m = Image.new("RGBA", (w, h), (0, 0, 0, 255))        # đục toàn bộ
    d = ImageDraw.Draw(m)
    d.rectangle([w // 2 - 160, h // 2 - 160, w // 2 + 160, h // 2 + 160], fill=(0, 0, 0, 0))  # lỗ trong suốt
    m.save(path)


def id_card(path):
    # Thẻ ID GIẢ LẬP, rõ ràng là demo (không mạo danh giấy tờ thật).
    w, h = 1000, 640
    img = Image.new("RGB", (w, h), (238, 242, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 90], fill=(10, 102, 194))
    d.text((30, 22), "CONTOSO DEMO ID CARD", font=font(40), fill=(255, 255, 255))
    d.rectangle([40, 150, 240, 420], fill=(200, 205, 215))         # ảnh chân dung (placeholder)
    d.text((70, 260), "PHOTO", font=font(32), fill=(90, 90, 90))
    rows = [
        ("Full name:", "NGUYEN VAN AN"),
        ("Date of birth:", "1990-05-12"),
        ("ID number:", "DEMO-0123456789"),
        ("Sex:", "M"),
        ("Nationality:", "Vietnam"),
        ("Date of expiry:", "2030-05-12"),
    ]
    y = 160
    for k, v in rows:
        d.text((300, y), k, font=font(28), fill=(70, 70, 70))
        d.text((560, y), v, font=font(28), fill=(10, 10, 10))
        y += 56
    img.save(path, quality=90)


def tone_wav(path, seconds=2.0, freq=440.0, rate=16000):
    # WAV tone hợp lệ 16kHz mono. ponytail: chỉ là tone -> STT trả rỗng; thu giọng thật nếu cần test STT.
    with wave.open(path, "w") as wv:
        wv.setnchannels(1)
        wv.setsampwidth(2)
        wv.setframerate(rate)
        frames = b"".join(
            struct.pack("<h", int(0.3 * 32767 * math.sin(2 * math.pi * freq * i / rate)))
            for i in range(int(seconds * rate))
        )
        wv.writeframes(frames)


def doc_pdf(path):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(path, pagesize=A4)
    W, H = A4
    c.setFont("Helvetica-Bold", 18)
    c.drawString(25 * mm, H - 30 * mm, "Contoso SmartHub X1 - Technical Overview")
    c.setFont("Helvetica", 11)
    lines = [
        "The Contoso SmartHub X1 is a central smart-home controller connecting lights,",
        "sensors and cameras through a single app. It supports Wi-Fi 6, Zigbee 3.0 and Matter.",
        "This document is sample data for Azure Document Intelligence layout analysis.",
    ]
    y = H - 42 * mm
    for ln in lines:
        c.drawString(25 * mm, y, ln)
        y -= 7 * mm
    # Bảng thông số -> layout model trả về tables.
    c.setFont("Helvetica-Bold", 12)
    c.drawString(25 * mm, y - 6 * mm, "Specifications")
    data = [("Property", "Value"), ("Power", "5V / 2A USB-C"),
            ("Memory", "2 GB RAM, 16 GB storage"), ("Weight", "180 g"),
            ("Operating temp", "0-40 C")]
    ty = y - 14 * mm
    x0, x1, rowh = 25 * mm, 95 * mm, 8 * mm
    for i, (a, b) in enumerate(data):
        c.rect(x0, ty - rowh, 70 * mm, rowh)
        c.rect(x1, ty - rowh, 70 * mm, rowh)
        c.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 10)
        c.drawString(x0 + 2 * mm, ty - rowh + 2.5 * mm, a)
        c.drawString(x1 + 2 * mm, ty - rowh + 2.5 * mm, b)
        ty -= rowh
    c.showPage()
    c.save()


def invoice_pdf(path):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(path, pagesize=A4)
    W, H = A4
    c.setFont("Helvetica-Bold", 22)
    c.drawString(25 * mm, H - 28 * mm, "INVOICE")
    c.setFont("Helvetica", 10)
    # Vendor + invoice meta -> prebuilt-invoice bắt VendorName, InvoiceId, InvoiceDate, Total...
    c.drawString(25 * mm, H - 40 * mm, "Contoso Ltd.")
    c.drawString(25 * mm, H - 45 * mm, "123 Le Loi, District 1, Ho Chi Minh City")
    c.drawString(25 * mm, H - 50 * mm, "support@contoso.vn")
    c.drawRightString(W - 25 * mm, H - 40 * mm, "Invoice Number: INV-2026-0042")
    c.drawRightString(W - 25 * mm, H - 45 * mm, "Invoice Date: 2026-11-20")
    c.drawRightString(W - 25 * mm, H - 50 * mm, "Due Date: 2026-12-20")
    c.drawString(25 * mm, H - 62 * mm, "Bill To: Fabrikam Inc., 456 Nguyen Hue, Ho Chi Minh City")
    # Bảng line items
    items = [("Description", "Qty", "Unit Price", "Amount"),
             ("SmartHub X1", "2", "1,990,000", "3,980,000"),
             ("Motion Sensor", "4", "250,000", "1,000,000"),
             ("USB-C Adapter", "2", "120,000", "240,000")]
    y = H - 75 * mm
    cols = [25 * mm, 110 * mm, 135 * mm, 165 * mm]
    for i, row in enumerate(items):
        c.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 10)
        for x, cell in zip(cols, row):
            (c.drawRightString(x + 20 * mm, y, cell) if x != cols[0] else c.drawString(x, y, cell))
        y -= 8 * mm
    c.line(25 * mm, y + 3 * mm, W - 25 * mm, y + 3 * mm)
    c.setFont("Helvetica", 10)
    c.drawRightString(cols[2] + 20 * mm, y - 3 * mm, "Subtotal:")
    c.drawRightString(cols[3] + 20 * mm, y - 3 * mm, "5,220,000")
    c.drawRightString(cols[2] + 20 * mm, y - 10 * mm, "Tax (8%):")
    c.drawRightString(cols[3] + 20 * mm, y - 10 * mm, "417,600")
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(cols[2] + 20 * mm, y - 18 * mm, "Total Due (VND):")
    c.drawRightString(cols[3] + 20 * mm, y - 18 * mm, "5,637,600")
    c.showPage()
    c.save()


base = scene(os.path.join(ASSETS, "sample_image.jpg"))
base.save(os.path.join(ASSETS, "sample_image.png"))
mask(os.path.join(ASSETS, "sample_mask.png"), base.size)
id_card(os.path.join(ASSETS, "sample_id.jpg"))
tone_wav(os.path.join(ASSETS, "sample_audio.wav"))
doc_pdf(os.path.join(ASSETS, "sample_document.pdf"))
invoice_pdf(os.path.join(ASSETS, "sample_invoice.pdf"))
print("OK ->", sorted(f for f in os.listdir(ASSETS) if not f.startswith(".") and f != "output"))
