#!/usr/bin/env python3
"""
Logger - Cấu hình structured logging cho ứng dụng.

Hỗ trợ:
- JSON format cho production (dễ parse bởi ELK/Grafana)
- Readable format cho development (dễ đọc trên terminal)
- Request logging middleware cho FastAPI
- Request ID tracing
"""

import json
import logging
import sys
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# ============================================================
# Custom Formatter
# ============================================================


class _ReadableFormatter(logging.Formatter):
    """
    Formatter dễ đọc cho development.

    Output: [LEVEL] module - message {extra}
    """

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET

        # Thu thập extra fields (bỏ các field mặc định của logging)
        default_keys = {
            "name", "msg", "args", "created", "relativeCreated",
            "exc_info", "exc_text", "stack_info", "lineno",
            "funcName", "pathname", "filename", "module",
            "levelno", "levelname", "msecs", "message",
            "taskName", "processName", "process", "thread",
            "threadName",
        }
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in default_keys and not k.startswith("_")
        }

        # Format message
        msg = super().format(record)
        extra_str = f" {extras}" if extras else ""

        return f"{color}[{record.levelname:>7}]{reset} {record.name} - {msg}{extra_str}"


class _JsonFormatter(logging.Formatter):
    """
    JSON formatter cho production.

    Output: {"timestamp": "...", "level": "...", "module": "...", "message": "...", ...}
    """

    def format(self, record: logging.LogRecord) -> str:
        # Thu thập extra fields
        default_keys = {
            "name", "msg", "args", "created", "relativeCreated",
            "exc_info", "exc_text", "stack_info", "lineno",
            "funcName", "pathname", "filename", "module",
            "levelno", "levelname", "msecs", "message",
            "taskName", "processName", "process", "thread",
            "threadName",
        }
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in default_keys and not k.startswith("_")
        }

        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            **extras,
        }

        # Thêm exception info nếu có
        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, default=str)


# ============================================================
# Logger Setup
# ============================================================


def setup_logging(level: str = "INFO", json_format: bool = False) -> None:
    """
    Thiết lập logging cho toàn bộ ứng dụng.

    Args:
        level: Mức log - "DEBUG" | "INFO" | "WARNING" | "ERROR"
        json_format: True = JSON format (production), False = readable (development)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Xóa handlers cũ
    root_logger.handlers.clear()

    # Tạo handler mới
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    if json_format:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(_ReadableFormatter())

    root_logger.addHandler(handler)

    # Giảm noise từ các thư viện bên thứ ba
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Lấy logger instance theo tên module.

    Args:
        name: Tên module (thường dùng __name__)

    Returns:
        Logger instance đã cấu hình
    """
    return logging.getLogger(name)


# ============================================================
# Request Logging Middleware
# ============================================================


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware ghi log mỗi HTTP request.

    Ghi nhận: method, path, status_code, processing_time, request_id.
    Tự động gắn request_id (UUID) vào mỗi request để trace.
    """

    def __init__(self, app: FastAPI) -> None:
        super().__init__(app)
        self._logger = get_logger("http")

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Xử lý request: ghi log trước và sau khi xử lý."""
        # Sinh request_id duy nhất
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Bắt đầu đo thời gian
        start_time = time.time()

        # Gọi endpoint
        response = await call_next(request)

        # Tính thời gian xử lý
        process_time_ms = round((time.time() - start_time) * 1000, 2)

        # Ghi log (bỏ qua health check để giảm noise)
        if request.url.path != "/":
            self._logger.info(
                f"{request.method} {request.url.path} → {response.status_code} "
                f"({process_time_ms}ms)",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                    "process_time_ms": process_time_ms,
                },
            )

        # Thêm request_id vào response header để client trace
        response.headers["X-Request-ID"] = request_id

        return response
