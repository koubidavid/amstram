import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

_database_url = os.environ.get("DATABASE_URL", settings.database_url)
_connect_args = {"check_same_thread": False} if _database_url.startswith("sqlite") else {}
engine = create_engine(_database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
