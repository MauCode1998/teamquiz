#!/usr/bin/env python3
"""Script to create test user in database"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from db_operations import create_user, is_username_taken
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_user():
    username = "Testbenutzer"
    password = "test123456"
    
    # Check if user already exists
    if is_username_taken(username):
        print(f"User '{username}' already exists!")
        return
    
    # Hash the password
    hashed_password = pwd_context.hash(password)
    
    # Create the user
    result = create_user(username, hashed_password)
    
    if isinstance(result, str):
        print(f"Error: {result}")
    else:
        print(f"Test user '{username}' created successfully!")
        print(f"Username: {username}")
        print(f"Password: {password}")

if __name__ == "__main__":
    create_test_user()