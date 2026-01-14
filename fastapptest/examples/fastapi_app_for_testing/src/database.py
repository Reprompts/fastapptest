# database.py
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

Base = declarative_base()
engine = None
SessionLocal = None

if settings.DATABASE_TYPE.lower() == "sql":
    try:
        db_url = settings.DATABASE_URL
        # make relative SQLite paths absolute if you ever switch to file-based
        if db_url.startswith("sqlite:///"):
            rel = db_url.replace("sqlite:///", "")
            abs_path = Path(__file__).resolve().parent / rel
            db_url = f"sqlite:///{abs_path}"
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False}
            if db_url.startswith("sqlite")
            else {}
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        logging.info("🔌 SQL engine initialized")
    except SQLAlchemyError as e:
        logging.warning(f"⚠️ SQL init failed: {e}")
        engine = None
        SessionLocal = None
else:
    logging.info("🚫 DATABASE_TYPE != 'sql'; skipping SQL init")


def get_db():
    """
    FastAPI dependency – yields a SQLAlchemy session or a Motor client DB.
    If init failed, yields None so app never crashes on startup.
    """
    if settings.DATABASE_TYPE.lower() == "sql" and SessionLocal:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        # MongoDB path (async)
        try:
            client = AsyncIOMotorClient(settings.DATABASE_URL)
            db = client[settings.DATABASE_NAME]
        except Exception as e:
            logging.warning(f"[database] MongoDB connect failed: {e}")
            yield None
            return

        try:
            yield db
        finally:
            client.close()
