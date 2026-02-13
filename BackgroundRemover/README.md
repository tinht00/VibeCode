# 🎨 Background Remover Web App

Ứng dụng web xóa nền ảnh chuyên nghiệp sử dụng Python (OpenCV + Pillow) và Vue 3.

## ✨ Tính năng

- **Xóa nền tự động** - AI tự chọn phương pháp tốt nhất
- **Xóa theo màu** - Xóa nền đơn sắc (trắng, xanh lá, v.v.)
- **Edge Detection** - Phát hiện cạnh chủ thể
- **GrabCut** - Thuật toán phân đoạn OpenCV
- **Thay nền** - Đổi nền bằng màu sắc
- **Tinh chỉnh** - Feather, expand, contract mask
- **Tải xuống** - Xuất PNG/WEBP/JPEG

## 🛠 Tech Stack

| Layer | Công nghệ |
|-------|----------|
| Backend | Python 3.10+, FastAPI, OpenCV, Pillow |
| Frontend | Vue 3, Vite, Pinia, TailwindCSS |
| Giao diện | Dark Glassmorphism, Animated Orbs |

## 🚀 Cài đặt & Chạy

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
# Server chạy tại http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App chạy tại http://localhost:5173
```

## 📁 Cấu trúc

```
BackgroundRemover/
├── backend/
│   ├── main.py                  # FastAPI server
│   ├── background_remover.py    # Core xử lý ảnh
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.vue              # Layout chính
│   │   ├── stores/imageStore.js # Pinia state
│   │   └── components/
│   │       ├── ImageUploader.vue
│   │       ├── ToolPanel.vue
│   │       └── ImagePreview.vue
│   └── ...config files
└── README.md
```

## 📝 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/upload` | Upload ảnh |
| POST | `/api/remove-background` | Xóa nền |
| POST | `/api/replace-background` | Thay nền |
| POST | `/api/refine` | Tinh chỉnh mask |
| GET | `/api/download/{file_id}` | Tải kết quả |
| GET | `/api/preview/{file_id}` | Xem preview |
