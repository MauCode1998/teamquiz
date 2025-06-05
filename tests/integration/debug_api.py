import requests
from datetime import datetime

# Create a test user
timestamp = datetime.now().microsecond
user_data = {
    "username": f"debuguser{timestamp}",
    "email": f"debug{timestamp}@test.com",
    "password": "testpass123"
}

print("Creating user...")
response = requests.post("http://localhost:8000/register", json=user_data)
print(f"Register response: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Create group
print("\nCreating group...")
group_name = f"DebugGroup{timestamp}"
response = requests.post(
    "http://localhost:8000/gruppe-erstellen",
    json={"gruppen_name": group_name},
    headers=headers
)
print(f"Group response: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")

# Create subject
print("\nCreating subject...")
subject_name = f"DebugSubject{timestamp}"
response = requests.post(
    "http://localhost:8000/fach-erstellen",
    json={"fach_name": subject_name, "gruppen_name": group_name},
    headers=headers
)
print(f"Subject response: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")

# Create flashcard
print("\nCreating flashcard...")
response = requests.post(
    "http://localhost:8000/flashcard/create",
    json={
        "frage": "Test question?",
        "antworten": [
            {"text": "Answer 1", "is_correct": False},
            {"text": "Answer 2", "is_correct": True},
            {"text": "Answer 3", "is_correct": False},
            {"text": "Answer 4", "is_correct": False}
        ],
        "fach": subject_name,
        "gruppe": group_name
    },
    headers=headers
)
print(f"Flashcard response: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")

# Create lobby
print("\nCreating lobby...")
response = requests.post(
    "http://localhost:8000/api/lobby/create",
    json={
        "subject_name": subject_name,
        "group_name": group_name
    },
    headers=headers
)
print(f"Lobby response: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    print(f"Success: {response.json()}")