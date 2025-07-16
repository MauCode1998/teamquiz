import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

test_db = os.getenv("TEST_DATABASE")
if test_db:
    DATABASE_URL = f"sqlite:///./{test_db}"
else:
    DATABASE_URL = "sqlite:///./teamquiz.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_size=20, 
    max_overflow=40,  
    pool_pre_ping=True, 
    pool_recycle=3600
)
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
