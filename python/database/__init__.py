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
engine = get_db_engine()
SessionM = sessionmaker(bind=engine)
# Create a session


def get_db():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME
    )
    return conn


def get_session():
    """
    Get a new database session.
    """

    return SessionM()
