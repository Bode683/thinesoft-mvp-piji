from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL configuration
# Prefer explicit DATABASE_URL if provided; otherwise, construct from POSTGRES_* env vars
_explicit_db_url = os.getenv("DATABASE_URL")
if _explicit_db_url:
    DATABASE_URL = _explicit_db_url
else:
    PG_USER = os.getenv("POSTGRES_USER", "postgres")
    PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    PG_DB = os.getenv("POSTGRES_DB", "postgres")
    PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
    PG_PORT = os.getenv("POSTGRES_PORT", "5432")
    DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,   # Recycle connections every hour
    echo=False           # Set to True for SQL query debugging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()
