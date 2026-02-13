---
description: Quy trình khởi chạy dự án BackgroundRemover trong môi trường development
---

# /dev - Chạy Development Server

Quy trình khởi chạy backend + frontend cho development.

## Yêu cầu
- Python 3.10+ (có pip)
- Node.js 18+ (có npm)

## Bước 1: Cài đặt Backend dependencies
// turbo
```bash
cd d:\Tinht00_Workspace\VibeCode\BackgroundRemover\backend
pip install -r requirements.txt
```

## Bước 2: Khởi chạy FastAPI server
```bash
cd d:\Tinht00_Workspace\VibeCode\BackgroundRemover\backend
python main.py
```
> Server chạy tại `http://localhost:8000`
> API docs: `http://localhost:8000/docs` (Swagger UI)

## Bước 3: Cài đặt Frontend dependencies
// turbo
```bash
cd d:\Tinht00_Workspace\VibeCode\BackgroundRemover\frontend
npm install
```

## Bước 4: Khởi chạy Vite dev server
```bash
cd d:\Tinht00_Workspace\VibeCode\BackgroundRemover\frontend
npm run dev
```
> App chạy tại `http://localhost:5173`
> API proxy: `/api/*` → `http://localhost:8000/api/*`

## Bước 5: Mở trình duyệt
Mở `http://localhost:5173` để sử dụng ứng dụng.

## Lưu ý
- Backend phải chạy **trước** Frontend (Vite proxy cần backend).
- Nếu thay đổi file Python, server FastAPI **tự động reload**.
- Nếu thay đổi file Vue, Vite dev server **tự động HMR (Hot Module Replacement)**.
