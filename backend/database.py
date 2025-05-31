import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use test database if TEST_DATABASE environment variable is set
test_db = os.getenv("TEST_DATABASE")
if test_db:
    DATABASE_URL = f"sqlite:///./{test_db}"
else:
    DATABASE_URL = "sqlite:///./teamquiz.db"

engine = create_engine(DATABASE_URL,connect_args={"check_same_thread":False})
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
