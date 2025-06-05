import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use test database if TEST_DATABASE environment variable is set
test_db = os.getenv("TEST_DATABASE")
if test_db:
    DATABASE_URL = f"sqlite:///./{test_db}"
else:
    DATABASE_URL = "sqlite:///./teamquiz.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_size=20,  # Increase from default 5
    max_overflow=40,  # Increase from default 10
    pool_pre_ping=True,  # Test connections before using
    pool_recycle=3600  # Recycle connections after 1 hour
)
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
