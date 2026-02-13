#!/usr/bin/env python3
"""
Integration Tests - Kiểm thử API endpoints.

Kiểm tra:
- Health check
- Upload ảnh (thành công và lỗi)
- Xóa nền (các phương pháp)
- Thay nền, tinh chỉnh
- Download, preview
- Xóa session
- Error response format chuẩn
"""

import io

import pytest
from PIL import Image
from fastapi.testclient import TestClient


class TestHealthCheck:
    """Kiểm thử health check endpoint."""

    def test_root(self, client: TestClient) -> None:
        """GET / → 200 + success response."""
        response = client.get("/")
        data = response.json()

        assert response.status_code == 200
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["version"] == "1.1.0"


class TestUpload:
    """Kiểm thử upload ảnh."""

    def test_upload_valid_png(self, client: TestClient, test_image_path: str) -> None:
        """Upload PNG hợp lệ → 200 + file_id + preview."""
        with open(test_image_path, "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.png", f, "image/png")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "file_id" in data["data"]
        assert "preview" in data["data"]
        assert data["data"]["width"] == 100
        assert data["data"]["height"] == 100

    def test_upload_invalid_type(self, client: TestClient) -> None:
        """Upload file text → 400 + VALIDATION_ERROR."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_upload_jpeg(self, client: TestClient) -> None:
        """Upload JPEG hợp lệ → 200."""
        # Tạo ảnh JPEG in-memory
        img = Image.new("RGB", (50, 50), (128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        response = client.post(
            "/api/upload",
            files={"file": ("test.jpg", buf, "image/jpeg")},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True


class TestRemoveBackground:
    """Kiểm thử xóa nền."""

    def test_remove_auto(
        self, client: TestClient, uploaded_file_id: str
    ) -> None:
        """Xóa nền auto → 200 + result base64."""
        response = client.post(
            "/api/remove-background",
            data={"file_id": uploaded_file_id, "method": "auto"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data["data"]
        assert len(data["data"]["result"]) > 0  # base64 string

    def test_remove_color_method(
        self, client: TestClient, uploaded_file_id: str
    ) -> None:
        """Xóa nền bằng color method → 200."""
        response = client.post(
            "/api/remove-background",
            data={
                "file_id": uploaded_file_id,
                "method": "color",
                "color": "255,255,255",
                "tolerance": 30,
            },
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_remove_edge_method(
        self, client: TestClient, uploaded_file_id: str
    ) -> None:
        """Xóa nền bằng edge method → 200."""
        response = client.post(
            "/api/remove-background",
            data={
                "file_id": uploaded_file_id,
                "method": "edge",
                "threshold": 50,
            },
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_remove_grabcut_method(
        self, client: TestClient, uploaded_file_id: str
    ) -> None:
        """Xóa nền bằng grabcut method → 200."""
        response = client.post(
            "/api/remove-background",
            data={
                "file_id": uploaded_file_id,
                "method": "grabcut",
                "iterations": 1,
            },
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_remove_invalid_session(self, client: TestClient) -> None:
        """Xóa nền với file_id không tồn tại → 404 + SESSION_NOT_FOUND."""
        response = client.post(
            "/api/remove-background",
            data={"file_id": "khong-ton-tai", "method": "auto"},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "SESSION_NOT_FOUND"


class TestReplaceBackground:
    """Kiểm thử thay nền."""

    def test_replace_with_color(
        self, client: TestClient, uploaded_file_id: str
    ) -> None:
        """Thay nền bằng màu → 200."""
        # Xóa nền trước
        client.post(
            "/api/remove-background",
            data={"file_id": uploaded_file_id, "method": "auto"},
        )

        # Thay nền
        response = client.post(
            "/api/replace-background",
            data={"file_id": uploaded_file_id, "color": "0,0,255"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data["data"]

    def test_replace_invalid_session(self, client: TestClient) -> None:
        """Thay nền với session không tồn tại → 404."""
        response = client.post(
            "/api/replace-background",
            data={"file_id": "khong-ton-tai", "color": "255,0,0"},
        )

        assert response.status_code == 404


class TestRefine:
    """Kiểm thử tinh chỉnh."""

    def test_refine_feather(
        self, client: TestClient, uploaded_file_id: str
    ) -> None:
        """Tinh chỉnh feather → 200."""
        # Xóa nền trước
        client.post(
            "/api/remove-background",
            data={"file_id": uploaded_file_id, "method": "auto"},
        )

        # Tinh chỉnh
        response = client.post(
            "/api/refine",
            data={
                "file_id": uploaded_file_id,
                "feather": 3,
                "expand": 0,
                "contract": 0,
            },
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_refine_invalid_session(self, client: TestClient) -> None:
        """Tinh chỉnh session không tồn tại → 404."""
        response = client.post(
            "/api/refine",
            data={"file_id": "khong-ton-tai", "feather": 3},
        )

        assert response.status_code == 404


class TestDownloadAndPreview:
    """Kiểm thử download và preview."""

    def test_download_png(
        self, client: TestClient, uploaded_file_id: str
    ) -> None:
        """Download PNG → 200 + binary content."""
        response = client.get(
            f"/api/download/{uploaded_file_id}?format=png"
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_download_invalid_session(self, client: TestClient) -> None:
        """Download session không tồn tại → 404."""
        response = client.get("/api/download/khong-ton-tai?format=png")
        assert response.status_code == 404

    def test_preview(
        self, client: TestClient, uploaded_file_id: str
    ) -> None:
        """Preview → 200 + original và current base64."""
        response = client.get(f"/api/preview/{uploaded_file_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "original" in data["data"]
        assert "current" in data["data"]

    def test_preview_invalid_session(self, client: TestClient) -> None:
        """Preview session không tồn tại → 404."""
        response = client.get("/api/preview/khong-ton-tai")
        assert response.status_code == 404


class TestDeleteSession:
    """Kiểm thử xóa session."""

    def test_delete_existing(
        self, client: TestClient, uploaded_file_id: str
    ) -> None:
        """Xóa session tồn tại → 200."""
        response = client.delete(f"/api/session/{uploaded_file_id}")

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Session đã bị xóa → preview phải trả lỗi
        preview_response = client.get(f"/api/preview/{uploaded_file_id}")
        assert preview_response.status_code == 404

    def test_delete_non_existing(self, client: TestClient) -> None:
        """Xóa session không tồn tại → 200 (idempotent)."""
        response = client.delete("/api/session/khong-ton-tai")
        assert response.status_code == 200


class TestErrorResponseFormat:
    """Kiểm thử error response format chuẩn."""

    def test_error_has_standard_format(self, client: TestClient) -> None:
        """
        Mọi error response phải có format:
        {"success": false, "error": {"code": "...", "message": "..."}}
        """
        response = client.post(
            "/api/remove-background",
            data={"file_id": "khong-ton-tai", "method": "auto"},
        )

        data = response.json()

        # Kiểm tra cấu trúc
        assert "success" in data
        assert data["success"] is False
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]

        # Code phải là string không rỗng
        assert isinstance(data["error"]["code"], str)
        assert len(data["error"]["code"]) > 0

        # Message phải là string không rỗng
        assert isinstance(data["error"]["message"], str)
        assert len(data["error"]["message"]) > 0

    def test_success_has_standard_format(
        self, client: TestClient, test_image_path: str
    ) -> None:
        """
        Mọi success response phải có format:
        {"success": true, "data": {...}, "message": "..."}
        """
        with open(test_image_path, "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.png", f, "image/png")},
            )

        data = response.json()

        # Kiểm tra cấu trúc
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        assert "message" in data
