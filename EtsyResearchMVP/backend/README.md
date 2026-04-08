# Etsy Research MVP Backend

API FastAPI cho ứng dụng tối ưu listing Etsy nội bộ.

## Chạy local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Chạy test

```bash
pytest
```
