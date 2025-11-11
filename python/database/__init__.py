import os

import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tools.encryption import decrypt_password
from tools.logger import get_logger

logger = get_logger(__name__)
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = decrypt_password(os.getenv("DB_PASSWORD"))
DB_NAME = os.getenv("DB_NAME")
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
SESSION_END_HOUR = int(os.getenv("SESSION_END_HOUR", 17))
SESSION_START_HOUR = int(os.getenv("SESSION_START_HOUR", 9))


def get_db_engine():
    db_no_pass_url = (
        f"postgresql+psycopg2://{DB_USER}:******@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    logger.info("Creating database engine with URL: %s", db_no_pass_url)
    engine = create_engine(DATABASE_URL)
    return engine


# Define the table metadata
logger.info("Initializing database engine and session maker")
engine = get_db_engine()
SessionM = sessionmaker(bind=engine)
# Create a session


def get_db():
    """
    Get a psycopg2 database connection.
    
    Returns:
        psycopg2.connection: Database connection
    """
    logger.debug(f"Creating psycopg2 connection to {DB_HOST}:{DB_PORT}/{DB_NAME}")
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME
        )
        logger.debug("Successfully created psycopg2 connection")
        return conn
    except Exception as e:
        logger.error(f"Failed to create psycopg2 connection: {e}")
        raise


def get_session():
    """
    Get a new database session.
    
    Returns:
        sqlalchemy.orm.Session: Database session
    """
    logger.debug("Creating new SQLAlchemy session")
    try:
        session = SessionM()
        logger.debug("Successfully created SQLAlchemy session")
        return session
    except Exception as e:
        logger.error(f"Failed to create SQLAlchemy session: {e}")
        raise
