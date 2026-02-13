#!/usr/bin/env python3
"""
Conftest - Test fixtures dùng chung cho test suite.

Cung cấp:
- test_image_path: Tạo ảnh test tạm thời
- client: FastAPI TestClient
- uploaded_file_id: Upload ảnh test → trả về file_id
"""

import os
import tempfile
from typing import Generator

import pytest
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

# Đặt môi trường test trước khi import app
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["CORS_ORIGINS"] = "http://localhost:5173,http://localhost:3000"
os.environ["SESSION_TTL_SECONDS"] = "60"
os.environ["MAX_SESSIONS"] = "10"

from main import app, sessions


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Tạo FastAPI TestClient.

    Tự động dọn dẹp sessions sau mỗi test.

    Yields:
        TestClient instance
    """
    with TestClient(app) as c:
        yield c

    # Dọn dẹp toàn bộ sessions sau mỗi test
    sessions._store.clear()


@pytest.fixture
def test_image_path() -> Generator[str, None, None]:
    """
    Tạo file ảnh test tạm thời (100x100 RGB, nền trắng, hình vuông đỏ ở giữa).

    File sẽ tự động xóa sau khi test hoàn tất.

    Yields:
        Đường dẫn tới file ảnh test
    """
    # Tạo ảnh 100x100 nền trắng
    img = Image.new("RGB", (100, 100), (255, 255, 255))

    # Vẽ hình vuông đỏ ở giữa (30x30)
    pixels = img.load()
    for x in range(35, 65):
        for y in range(35, 65):
            pixels[x, y] = (255, 0, 0)

    # Lưu ra file tạm
    with tempfile.NamedTemporaryFile(
        suffix=".png", delete=False
    ) as f:
        img.save(f, format="PNG")
        filepath = f.name

    yield filepath

    # Dọn dẹp
    if os.path.exists(filepath):
        os.unlink(filepath)


@pytest.fixture
def test_image_rgba_path() -> Generator[str, None, None]:
    """
    Tạo file ảnh test RGBA tạm thời (100x100, nền transparent).

    Yields:
        Đường dẫn tới file ảnh RGBA test
    """
    img = Image.new("RGBA", (100, 100), (255, 255, 255, 255))

    # Vẽ vùng transparent ở góc
    pixels = img.load()
    for x in range(0, 30):
        for y in range(0, 30):
            pixels[x, y] = (0, 0, 0, 0)

    with tempfile.NamedTemporaryFile(
        suffix=".png", delete=False
    ) as f:
        img.save(f, format="PNG")
        filepath = f.name

    yield filepath

    if os.path.exists(filepath):
        os.unlink(filepath)


@pytest.fixture
def uploaded_file_id(client: TestClient, test_image_path: str) -> str:
    """
    Upload ảnh test và trả về file_id.

    Args:
        client: TestClient fixture
        test_image_path: Đường dẫn ảnh test

    Returns:
        file_id dùng cho các request tiếp theo
    """
    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test.png", f, "image/png")},
        )

    data = response.json()
    return data.get("data", data).get("file_id", data.get("file_id"))
