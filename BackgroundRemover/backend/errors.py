#!/usr/bin/env python3
"""
Errors - Hệ thống xử lý lỗi chuẩn hóa cho ứng dụng.

Cung cấp:
- Base exception class AppError với error_code và status_code
- Các exception cụ thể cho từng loại lỗi
- Exception handler đăng ký vào FastAPI
- Response format thống nhất cho success và error
"""

from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from logger import get_logger

logger = get_logger(__name__)


# ============================================================
# Response Helpers - Format response chuẩn
# ============================================================


def success_response(
    data: Any = None,
    message: str = "Thành công",
) -> Dict[str, Any]:
    """
    Tạo response thành công chuẩn.

    Args:
        data: Dữ liệu trả về (dict, list, hoặc bất kỳ)
        message: Thông báo thành công (tiếng Việt)

    Returns:
        Dict theo format chuẩn: {"success": true, "data": ..., "message": "..."}
    """
    response: Dict[str, Any] = {
        "success": True,
        "message": message,
    }
    if data is not None:
        response["data"] = data
    return response


# ============================================================
# Custom Exceptions
# ============================================================


class AppError(Exception):
    """
    Base exception cho ứng dụng.

    Mọi lỗi nghiệp vụ (business logic) phải kế thừa từ class này.

    Attributes:
        error_code: Mã lỗi dạng UPPER_SNAKE_CASE (vd: "SESSION_NOT_FOUND")
        message: Thông báo lỗi thân thiện (tiếng Việt)
        status_code: HTTP status code tương ứng
        details: Thông tin bổ sung (tùy chọn)
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class SessionNotFoundError(AppError):
    """Lỗi khi không tìm thấy phiên xử lý ảnh."""

    def __init__(self, file_id: str) -> None:
        super().__init__(
            error_code="SESSION_NOT_FOUND",
            message=f"Không tìm thấy phiên làm việc: {file_id}",
            status_code=404,
            details={"file_id": file_id},
        )


class ImageProcessingError(AppError):
    """Lỗi trong quá trình xử lý ảnh."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            error_code="IMAGE_PROCESSING_ERROR",
            message=f"Lỗi xử lý ảnh: {message}",
            status_code=500,
            details=details,
        )


class ValidationError(AppError):
    """Lỗi dữ liệu đầu vào không hợp lệ."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            status_code=400,
            details=details,
        )


class NoResultError(AppError):
    """Lỗi khi chưa có kết quả để thao tác."""

    def __init__(self, file_id: str) -> None:
        super().__init__(
            error_code="NO_RESULT",
            message="Chưa có ảnh kết quả. Vui lòng xóa nền trước.",
            status_code=400,
            details={"file_id": file_id},
        )


# ============================================================
# Exception Handlers - Đăng ký vào FastAPI
# ============================================================


def register_exception_handlers(app: FastAPI) -> None:
    """
    Đăng ký exception handlers vào FastAPI app.

    Chuyển đổi mọi AppError thành JSON response thống nhất.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Xử lý AppError → JSON response chuẩn."""
        logger.warning(
            f"AppError: [{exc.error_code}] {exc.message}",
            extra={
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "path": str(request.url.path),
            },
        )

        error_body: Dict[str, Any] = {
            "code": exc.error_code,
            "message": exc.message,
        }
        if exc.details:
            error_body["details"] = exc.details

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": error_body,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Xử lý exception không mong đợi → JSON response an toàn."""
        logger.exception(
            f"Lỗi không mong đợi: {exc}",
            extra={"path": str(request.url.path)},
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Đã xảy ra lỗi nội bộ. Vui lòng thử lại sau.",
                },
            },
        )
