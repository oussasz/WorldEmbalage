from __future__ import annotations
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from .settings import settings
from loguru import logger
from sqlalchemy.exc import OperationalError
from pathlib import Path

# Initialize engine with fallback logic
_engine = None
try:
    _engine = create_engine(
        settings.dsn(),
        echo=settings.db_echo,
        pool_pre_ping=True,
        pool_recycle=3600,
        future=True
    )
    with _engine.connect() as _conn:
        _conn.execute(text('SELECT 1'))
    engine = _engine
except OperationalError as e:
    logger.error("Primary DB connection failed ({}). Falling back to SQLite.", e)
    fallback_path = (Path(settings.reports_dir).parent / 'world_embalage_fallback.db').resolve()
    engine = create_engine(f'sqlite:///{fallback_path}', future=True)
    logger.warning("Using fallback SQLite database at {}", fallback_path)

SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True))


def get_session():
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
    except Exception as exc:
        logger.exception("DB session error: {}", exc)
        db.rollback()
        raise
    finally:
        db.close()

__all__ = ['engine', 'SessionLocal', 'get_session']
