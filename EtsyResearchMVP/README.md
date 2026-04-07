# Etsy Research MVP

Web app nội bộ hỗ trợ kết nối shop Etsy, đồng bộ listing, audit chất lượng SEO cơ bản và benchmark keyword mức nhẹ.

## Cấu trúc

```text
EtsyResearchMVP/
├── backend/   # FastAPI + SQLAlchemy + Alembic
├── frontend/  # Vue 3 + Vite + Pinia + Router
├── infra/     # Docker Compose và env mẫu
├── docs/      # Hướng dẫn OAuth Etsy, flow sync/audit
└── .agent/    # Rules và workflow nội bộ cho app mới
```

## Chạy local

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Test backend

```bash
cd backend
pytest
```
