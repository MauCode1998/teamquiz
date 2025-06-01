"""Test data generation utilities"""

import random
import string


def generate_test_user(prefix="testuser"):
    """Generate unique test user data"""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return {
        "username": f"{prefix}{suffix}",
        "email": f"{prefix}{suffix}@example.com",
        "password": "TestPassword123!"
    }


def generate_test_group(prefix="TestGroup"):
    """Generate unique test group name"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}{suffix}"


def generate_test_subject(prefix="TestSubject"):
    """Generate unique test subject name"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}{suffix}"


def generate_test_flashcard():
    """Generate test flashcard data"""
    suffix = ''.join(random.choices(string.digits, k=3))
    return {
        "question": f"Test Question {suffix}?",
        "answers": [
            f"Correct Answer {suffix}",
            f"Wrong Answer A {suffix}",
            f"Wrong Answer B {suffix}",
            f"Wrong Answer C {suffix}"
        ],
        "correct_index": 0
    }


# Pre-defined test scenarios
SAMPLE_USERS = [
    {"username": "alice", "email": "alice@example.com", "password": "Alice123!"},
    {"username": "bob", "email": "bob@example.com", "password": "Bob123!"},
    {"username": "charlie", "email": "charlie@example.com", "password": "Charlie123!"}
]

SAMPLE_GROUPS = ["Mathematik", "Informatik", "Physik", "Chemie"]

SAMPLE_SUBJECTS = ["Algebra", "Analysis", "Geometrie", "Statistik"]

SAMPLE_FLASHCARDS = [
    {
        "question": "Was ist 2 + 2?",
        "answers": ["4", "3", "5", "6"],
        "correct_index": 0
    },
    {
        "question": "Welche Farbe hat der Himmel?",
        "answers": ["Blau", "Rot", "Grün", "Gelb"],
        "correct_index": 0
    },
    {
        "question": "Wie viele Tage hat eine Woche?",
        "answers": ["7", "5", "6", "8"],
        "correct_index": 0
    }
]