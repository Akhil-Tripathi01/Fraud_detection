"""
Database Configuration
SQLAlchemy setup for PostgreSQL (with SQLite fallback for local demo)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# ─── Database URL ────────────────────────────────────────────────────────────
# Uses PostgreSQL if DATABASE_URL is set, otherwise falls back to SQLite for demo
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./fraud_detection.db"  # SQLite for easy local demo
)

# SQLite needs special connect_args
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set True to see SQL queries in console
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency injection for FastAPI routes.
    Yields a database session and ensures it is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
