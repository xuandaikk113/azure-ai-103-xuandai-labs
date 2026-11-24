# assets/ — dữ liệu mẫu cho các lab

Để file mẫu vào đây rồi trỏ đường dẫn từ code lab. Thư mục `assets/output/` (kết quả sinh ra) đã được `.gitignore`.

Các file mẫu dưới đây **đã được sinh sẵn** (sinh lại bằng script ở cuối). Tên khớp đúng đường dẫn trong code lab:

| File | Lab dùng |
|------|----------|
| `finetune_train.jsonl` | 01/06 fine-tuning (10 cặp chat tiếng Việt, format `messages`) |
| `product_info.md` | 03/03 agent File Search (index tài liệu sản phẩm) |
| `weather_openapi.json` | 03/08 agent OpenAPI tool (spec 3.0, anonymous, trỏ `wttr.in`) |
| `sample_image.jpg` | 02/05 multimodal · 07/01 image analysis · 07/02 object detection |
| `sample_image.png` + `sample_mask.png` | 07/08 image generation/editing (inpainting) |
| `sample_audio.wav` | 07/06 speech STT |
| `sample_document.pdf` | 08/01 Document Intelligence layout (có bảng) |
| `sample_invoice.pdf` | 08/02 Document Intelligence prebuilt-invoice |
| `sample_id.jpg` | 08/02 Document Intelligence prebuilt-idDocument (thẻ demo giả lập) |

> **Lưu ý thực tế (2 file placeholder):**
> - `sample_audio.wav` là **tone 440Hz**, hợp lệ nhưng STT sẽ trả chuỗi rỗng. Muốn test STT thật: thu 1 câu giọng nói (hoặc dùng output TTS của chính lab 07/06) rồi ghi đè file này.
> - `sample_id.jpg` là thẻ **giả lập rõ ràng là demo** (không phải giấy tờ thật); prebuilt-idDocument trích xuất tốt nhất trên ảnh CMND/hộ chiếu thật.

Các lab RAG (06) **không đọc file local** — chúng truy vấn Azure AI Search index / knowledge base (dữ liệu nằm trên Azure), nên không có file mẫu ở đây.

Sinh lại toàn bộ file nhị phân (ảnh/PDF/audio) khi cần — không thêm dependency vào project:

```bash
uv run --with pillow --with reportlab python assets/gen_assets.py assets
```

> Dữ liệu tải về là **untrusted**: để trong `assets/`, không chạy interpreter từ trong thư mục này; truyền đường dẫn làm tham số.
