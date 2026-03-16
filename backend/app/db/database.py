import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

_database_url = os.environ.get("DATABASE_URL", settings.database_url)

# Handle SQLite for tests
_connect_args = {}
if _database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

# Neon requires SSL — strip channel_binding param that SQLAlchemy doesn't understand
if "channel_binding" in _database_url:
    _database_url = _database_url.split("&channel_binding")[0]

engine = create_engine(_database_url, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
