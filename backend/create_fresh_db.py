#!/usr/bin/env python3
"""
Create a fresh database with the current schema
"""
from database import engine
from models import Base

# Drop all tables and recreate them
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("Fresh database created successfully!")
print("The database is now empty and ready to use.")
print("Note: All previous data has been removed.")