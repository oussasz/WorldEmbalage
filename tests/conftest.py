import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
import models.suppliers  # noqa
import models.clients  # noqa
import models.plaques  # noqa
import models.orders  # noqa
import models.production  # noqa

@pytest.fixture()
def db_session():
    # Use SQLite in-memory for tests
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
