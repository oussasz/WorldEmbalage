from __future__ import annotations
from sqlalchemy import text
from config.database import engine
from models.base import Base
from loguru import logger


def init_db():
    """Create all tables. In production prefer migrations."""
    import models.suppliers  # noqa: F401
    import models.clients  # noqa: F401
    import models.plaques  # noqa: F401
    import models.orders  # noqa: F401
    import models.production  # noqa: F401

    logger.info("Création des tables de base de données si inexistantes...")
    Base.metadata.create_all(bind=engine)
    logger.info("Initialisation de la base de données terminée")


__all__ = ['init_db']
