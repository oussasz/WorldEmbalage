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


def _ensure_client_activity_column() -> None:
    """Ensure the optional 'activity' column exists on the clients table.
    This guards against environments where Alembic migrations haven't been applied yet.
    Safe to run multiple times.
    """
    try:
        dialect = engine.dialect.name.lower()
        with engine.connect() as conn:
            if dialect == 'sqlite':
                # Inspect columns via PRAGMA
                res = conn.execute(text("PRAGMA table_info(clients)"))
                cols = {row[1] for row in res.fetchall()}  # row[1] is the column name
                if 'activity' not in cols:
                    conn.execute(text("ALTER TABLE clients ADD COLUMN activity VARCHAR(128)"))
            elif dialect in ('mysql', 'mariadb'):
                # Check INFORMATION_SCHEMA
                check_sql = (
                    "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'clients' AND COLUMN_NAME = 'activity'"
                )
                exists = conn.execute(text(check_sql)).scalar() or 0
                if int(exists) == 0:
                    # IF NOT EXISTS is supported in MySQL 8, but use defensive check above for broad compatibility
                    conn.execute(text("ALTER TABLE clients ADD COLUMN activity VARCHAR(128) NULL"))
            # else: other dialects not used in this app; skip
    except Exception as exc:
        # Non-fatal: log and continue
        try:
            logger.warning("Schema guard skipped or failed: {}", exc)
        except Exception:
            pass


# Best-effort schema guard at import time (after engine is ready)
try:
    _ensure_client_activity_column()
except Exception:
    pass


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
