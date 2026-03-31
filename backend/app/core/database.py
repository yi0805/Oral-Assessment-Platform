"""Database engine, session factory, and shared ORM base class."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""



def get_db():
    """FastAPI dependency that yields a database session and closes it automatically."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
