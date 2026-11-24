# assets/ — dữ liệu mẫu cho các lab

Để file mẫu vào đây rồi trỏ đường dẫn từ code lab. Thư mục `assets/output/` (kết quả sinh ra) đã được `.gitignore`.

Gợi ý file cần có (tên tuỳ bạn, nhớ khớp với code):

| File | Lab dùng |
|------|----------|
| `sample_image.jpg` | 07 vision (image analysis, objects, multimodal chat) |
| `sample_invoice.pdf` | 08 document intelligence (invoice) |
| `sample_id.jpg` | 08 document intelligence (idDocument) |
| `sample_document.pdf` | 08 layout / content understanding |
| `sample_audio.wav` | 07 speech (STT), 08 content understanding (audio) |
| `sample_video.mp4` | 08 content understanding (video) |
| `sample_data.csv` | 03 agent code interpreter |
| `knowledge/*.md,*.pdf` | 06 RAG (ingest vào index/knowledge base) |

> Dữ liệu tải về là **untrusted**: để trong `assets/`, không chạy interpreter từ trong thư mục này; truyền đường dẫn làm tham số.
