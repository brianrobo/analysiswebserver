"""
Database session management with SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from api.core.config import settings


# Create SQLAlchemy engine
# Note: Using synchronous engine for simplicity (asyncpg requires C++ build tools)
# In production with Docker, you can use async: create_async_engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before using
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI to get database session

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database: create all tables

    Call this function once when starting the application
    """
    # Import models to register them with Base.metadata
    from api.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
