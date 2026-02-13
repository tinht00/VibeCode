#!/usr/bin/env python3
"""
Session Manager - Quản lý phiên xử lý ảnh với TTL và giới hạn số lượng.

Thay thế dict in-memory đơn giản bằng class có:
- TTL (Time-To-Live): Tự động xóa session hết hạn
- LRU Eviction: Xóa session cũ nhất khi vượt giới hạn
- Thread-safe: Dùng Lock bảo vệ truy cập đồng thời
- Interface sẵn sàng thay thế bằng Redis
"""

import time
import threading
from typing import Dict, Optional, Tuple

from background_remover import BackgroundRemover
from config import settings
from logger import get_logger

logger = get_logger(__name__)


class _SessionEntry:
    """
    Entry nội bộ lưu trữ session kèm metadata.

    Attributes:
        remover: Instance BackgroundRemover đang xử lý
        created_at: Thời điểm tạo (Unix timestamp)
        last_accessed: Thời điểm truy cập cuối (Unix timestamp)
    """

    __slots__ = ("remover", "created_at", "last_accessed")

    def __init__(self, remover: BackgroundRemover) -> None:
        now = time.time()
        self.remover = remover
        self.created_at: float = now
        self.last_accessed: float = now

    def touch(self) -> None:
        """Cập nhật thời điểm truy cập cuối."""
        self.last_accessed = time.time()

    def is_expired(self, ttl_seconds: int) -> bool:
        """
        Kiểm tra session đã hết hạn chưa.

        Args:
            ttl_seconds: Thời gian sống tối đa (giây)

        Returns:
            True nếu session đã quá TTL
        """
        return (time.time() - self.last_accessed) > ttl_seconds


class SessionManager:
    """
    Quản lý phiên xử lý ảnh.

    Hỗ trợ TTL, giới hạn session, và thread-safety.
    Sẵn sàng thay thế bằng Redis adapter khi chuyển sang production.

    Args:
        ttl_seconds: Thời gian sống tối đa cho mỗi session (giây)
        max_sessions: Số session tối đa đồng thời
    """

    def __init__(
        self,
        ttl_seconds: int = settings.SESSION_TTL_SECONDS,
        max_sessions: int = settings.MAX_SESSIONS,
    ) -> None:
        self._store: Dict[str, _SessionEntry] = {}
        self._lock = threading.Lock()
        self._ttl_seconds = ttl_seconds
        self._max_sessions = max_sessions

    def get(self, file_id: str) -> Optional[BackgroundRemover]:
        """
        Lấy BackgroundRemover theo file_id.

        Tự động xóa nếu session đã hết hạn.

        Args:
            file_id: ID phiên cần lấy

        Returns:
            BackgroundRemover instance hoặc None nếu không tồn tại / hết hạn
        """
        with self._lock:
            entry = self._store.get(file_id)
            if entry is None:
                return None

            # Kiểm tra TTL
            if entry.is_expired(self._ttl_seconds):
                logger.info(
                    "Session hết hạn, tự động xóa",
                    extra={"file_id": file_id},
                )
                del self._store[file_id]
                return None

            entry.touch()
            return entry.remover

    def set(self, file_id: str, remover: BackgroundRemover) -> None:
        """
        Lưu hoặc cập nhật session.

        Nếu vượt quá giới hạn, xóa session cũ nhất (LRU eviction).

        Args:
            file_id: ID phiên
            remover: BackgroundRemover instance cần lưu
        """
        with self._lock:
            # Dọn dẹp session hết hạn trước
            self._cleanup_expired_unsafe()

            # Nếu vẫn vượt giới hạn → xóa session cũ nhất
            while (
                len(self._store) >= self._max_sessions
                and file_id not in self._store
            ):
                oldest_id = self._find_oldest_unsafe()
                if oldest_id:
                    logger.info(
                        "Xóa session cũ nhất (LRU eviction)",
                        extra={"file_id": oldest_id},
                    )
                    del self._store[oldest_id]
                else:
                    break

            self._store[file_id] = _SessionEntry(remover)
            logger.debug(
                "Lưu session mới",
                extra={"file_id": file_id, "total_sessions": len(self._store)},
            )

    def delete(self, file_id: str) -> bool:
        """
        Xóa session theo file_id.

        Args:
            file_id: ID phiên cần xóa

        Returns:
            True nếu đã xóa, False nếu không tồn tại
        """
        with self._lock:
            if file_id in self._store:
                del self._store[file_id]
                logger.debug("Xóa session", extra={"file_id": file_id})
                return True
            return False

    def cleanup_expired(self) -> int:
        """
        Xóa tất cả sessions đã hết hạn.

        Returns:
            Số session đã xóa
        """
        with self._lock:
            return self._cleanup_expired_unsafe()

    def count(self) -> int:
        """Đếm tổng session đang hoạt động (bao gồm cả expired chưa dọn)."""
        with self._lock:
            return len(self._store)

    def _cleanup_expired_unsafe(self) -> int:
        """
        Xóa sessions hết hạn (KHÔNG thread-safe, gọi trong lock).

        Returns:
            Số session đã xóa
        """
        expired_ids = [
            fid
            for fid, entry in self._store.items()
            if entry.is_expired(self._ttl_seconds)
        ]

        for fid in expired_ids:
            del self._store[fid]

        if expired_ids:
            logger.info(
                f"Đã dọn dẹp {len(expired_ids)} session hết hạn",
                extra={"expired_count": len(expired_ids)},
            )

        return len(expired_ids)

    def _find_oldest_unsafe(self) -> Optional[str]:
        """
        Tìm session có last_accessed cũ nhất (KHÔNG thread-safe).

        Returns:
            file_id của session cũ nhất hoặc None nếu store rỗng
        """
        if not self._store:
            return None

        return min(
            self._store,
            key=lambda fid: self._store[fid].last_accessed,
        )
