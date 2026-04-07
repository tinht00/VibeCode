"""Quản lý engine và session SQLAlchemy."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _connect_args() -> dict:
    """Bổ sung connect args cho SQLite để tiện chạy local/test."""

    if settings.postgres_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    settings.postgres_url,
    future=True,
    connect_args=_connect_args(),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    """Dependency trả về session DB."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
