# Clipart Ops

Ứng dụng desktop Python + PySide6 để vận hành workspace clipart:
- quản lý cây thư mục chủ đề
- đóng gói bundle Etsy
- chuẩn bị khung metadata Etsy/Pinterest để chỉnh bằng AI ngoài
- xem và sửa CSV Pinterest, Markdown, JSON
- upload ảnh marketing lên Google Drive
- tạo CSV Pinterest theo hướng CSV-first

## Chạy local

```bash
cd clipart_ops
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
python -m clipart_ops.main
```

Hoặc tạo file `clipart_ops/.env.local` dựa trên `.env.example` để app tự nạp secret khi khởi động.

## Secrets cần có

- `GOOGLE_DRIVE_CLIENT_SECRET`: đường dẫn tới file OAuth Desktop Client JSON của Google Drive

## Lưu ý

- App không còn gọi Google AI. Metadata được tạo dưới dạng khung nội bộ để bạn chỉnh bằng Codex hoặc AI ngoài.
- Nếu thiếu thư viện hoặc secret Google Drive, app vẫn chạy được nhưng action upload Drive sẽ báo rõ điều kiện còn thiếu.
