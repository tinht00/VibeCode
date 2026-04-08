"""Thiết lập logging chung cho ứng dụng."""

import logging


def setup_logging() -> None:
    """Khởi tạo logging cơ bản cho toàn ứng dụng."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
