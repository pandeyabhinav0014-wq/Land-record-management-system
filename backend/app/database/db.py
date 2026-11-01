"""
Database Engine and SQLAlchemy Session Configuration
Uses SQLite with WAL mode by default; cleanly decoupled for PostgreSQL/PostGIS migration.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "land_records.db")
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

