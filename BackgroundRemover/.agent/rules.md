# Background Remover - Project Rules

Quy tắc riêng cho dự án Background Remover Web App. Kế thừa và bổ sung từ quy chuẩn toàn cục (`VibeCode/.agent/rules.md`).

## 1. Tổng quan dự án

**Background Remover** là ứng dụng web xóa/thay nền ảnh chuyên nghiệp.

| Layer | Stack | Vai trò |
|---|---|---|
| Backend | Python 3.10+ / FastAPI / OpenCV / Pillow | API xử lý ảnh |
| Frontend | Vue 3 / Vite / Pinia / TailwindCSS | Giao diện web |

## 2. Cấu trúc thư mục

```
BackgroundRemover/
├── backend/
│   ├── main.py                  # FastAPI server - Entry point
│   ├── background_remover.py    # Core class xử lý ảnh
│   ├── requirements.txt         # Python dependencies
│   ├── uploads/                 # Thư mục upload tạm (auto-tạo)
│   └── outputs/                 # Thư mục output tạm (auto-tạo)
├── frontend/
│   ├── index.html               # HTML entry
│   ├── package.json             # Node dependencies
│   ├── vite.config.js           # Vite config (proxy /api → :8000)
│   ├── tailwind.config.js       # TailwindCSS config (dark theme)
│   ├── postcss.config.js        # PostCSS config
│   └── src/
│       ├── main.js              # Vue entry point
│       ├── App.vue              # Layout chính (2-column)
│       ├── style.css            # Global styles + TailwindCSS
│       ├── stores/
│       │   └── imageStore.js    # Pinia store (state + API calls)
│       └── components/
│           ├── ImageUploader.vue    # Drag & Drop upload
│           ├── ToolPanel.vue        # Chọn method + tùy chỉnh
│           └── ImagePreview.vue     # Before/After preview
├── .agent/                      # Cấu hình AI agent
│   ├── rules.md                 # File này
│   └── workflows/
│       └── dev.md               # Quy trình chạy dev
└── README.md
```

## 3. Quy tắc Backend (Python FastAPI)

### API Convention
*   **Base URL**: `/api/`
*   **Naming**: Dùng kebab-case cho endpoints: `/api/remove-background`, `/api/replace-background`
*   **Request**: Dùng `Form(...)` cho parameters đơn giản, `File(...)` cho upload
*   **Response**: JSON format thống nhất:
    ```json
    {
      "file_id": "uuid",
      "result": "base64_string",
      "message": "Thông báo tiếng Việt"
    }
    ```
*   **Error**: Dùng `HTTPException` với `detail` tiếng Việt rõ ràng

### Code Style
*   **Type Hints**: Bắt buộc cho **mọi** function parameter và return type
*   **Docstring**: Google-style, viết bằng **tiếng Việt**
*   **Import order**: stdlib → third-party → local
*   **Function length**: Tối đa 50 dòng, tách nhỏ nếu vượt quá
*   **Naming**: snake_case cho functions/variables, PascalCase cho classes

### Xử lý ảnh
*   Ảnh luôn chuyển sang **RGBA mode** khi load
*   Mask dùng mode **L** (grayscale 0-255)
*   Output PNG mặc định để giữ transparency
*   JPEG: Tự động chuyển RGB + nền trắng (không hỗ trợ alpha)

## 4. Quy tắc Frontend (Vue 3 + Vite)

### Architecture
*   **Composition API** + `<script setup>` — TUYỆT ĐỐI không dùng Options API
*   **Pinia** cho state management — `imageStore.js` là store duy nhất
*   **Scoped CSS** cho components — Global CSS chỉ ở `style.css`

### Component Convention
*   Mỗi component phải có JSDoc comment ở đầu `<script setup>`
*   Props & Emits: Tường minh, có type annotation
*   Không hard-code API URL — dùng proxy qua Vite config

### Design System
*   **Theme**: Dark glassmorphism (`surface-900: #0f0a2e`)
*   **Accent**: Gradient tím-xanh (`#7c3aed → #22d3ee`)
*   **Typography**: Space Grotesk (headings) + DM Sans (body)
*   **Glass cards**: `backdrop-filter: blur(20px)` + border subtle
*   **Animations**: Stagger reveal, float, glow pulse

## 5. Quy trình phát triển

### Chạy Development
```bash
# Terminal 1: Backend
cd backend && pip install -r requirements.txt && python main.py

# Terminal 2: Frontend
cd frontend && npm install && npm run dev
```

### Ports
| Service | Port | URL |
|---|---|---|
| FastAPI Backend | 8000 | `http://localhost:8000` |
| Vite Dev Server | 5173 | `http://localhost:5173` |

### Flow xử lý
```
Upload ảnh → POST /api/upload → file_id
   ↓
Xóa nền → POST /api/remove-background → base64 result
   ↓
(Tùy chọn) Thay nền → POST /api/replace-background
(Tùy chọn) Tinh chỉnh → POST /api/refine
   ↓
Download → GET /api/download/{file_id}
```

## 6. Lưu ý quan trọng

*   **Session storage**: Đang dùng in-memory dict. Production cần chuyển sang Redis/DB.
*   **File cleanup**: Cần cron job xóa files tạm trong `uploads/` và `outputs/`.
*   **CORS**: Đang allow all (`*`). Production cần restrict origin.
*   **Image size limit**: Hiện tại kiểm tra ở frontend (20MB). Cần thêm validate ở backend.
