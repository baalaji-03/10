import os
import shutil
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

logger = logging.getLogger("pharmacy_app")
logging.basicConfig(level=logging.INFO)

Base = declarative_base()

def _get_sqlite_engine():
    is_vercel = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
    if is_vercel:
        sqlite_path = "/tmp/pharmacy.db"
        # Seed /tmp from existing pharmacy.db if available
        repo_db = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "pharmacy.db"
        )
        if not os.path.exists(sqlite_path) and os.path.exists(repo_db):
            try:
                shutil.copyfile(repo_db, sqlite_path)
                logger.info("Successfully copied seed database to /tmp/pharmacy.db")
            except Exception as e:
                logger.warning(f"Could not copy seed database to /tmp: {e}")
    else:
        sqlite_path = "./pharmacy.db"

    logger.info(f"Using SQLite database at {sqlite_path}")
    return create_engine(
        f"sqlite:///{sqlite_path}",
        connect_args={"check_same_thread": False}
    )

def get_database_engine():
    """
    Creates SQLAlchemy database engine.
    1. If explicit DATABASE_URL is set (and not pointing to localhost on Vercel), attempts MySQL connection.
    2. If MySQL is unreachable, DB_TYPE='sqlite', or running on Vercel without hosted DB, safely uses SQLite.
    """
    is_vercel = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
    raw_db_url = os.getenv("DATABASE_URL")

    # If DB_TYPE explicitly requested sqlite, or on Vercel with no remote DATABASE_URL configured
    if settings.DB_TYPE.lower() == "sqlite" or (is_vercel and not raw_db_url):
        return _get_sqlite_engine()

    # Determine MySQL connection URL
    database_url = raw_db_url or settings.DATABASE_URL
    if database_url.startswith("mysql://"):
        database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)

    # Prevent connecting to localhost when deployed on Vercel
    if is_vercel and ("localhost" in database_url or "127.0.0.1" in database_url):
        logger.warning("DATABASE_URL points to localhost on Vercel; falling back to /tmp/pharmacy.db")
        return _get_sqlite_engine()

    try:
        logger.info("Attempting database connection...")
        pool_kwargs = {
            "pool_pre_ping": True,
            "pool_recycle": 300 if is_vercel else 3600
        }
        if is_vercel:
            pool_kwargs["pool_size"] = 1
            pool_kwargs["max_overflow"] = 0

        mysql_engine = create_engine(database_url, **pool_kwargs)
        with mysql_engine.connect():
            pass  # Ping check
        logger.info("Successfully connected to MySQL database.")
        return mysql_engine
    except Exception as e:
        logger.warning(f"Database connection failed ({e}). Falling back to SQLite for uninterrupted operation.")
        return _get_sqlite_engine()

engine = get_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
