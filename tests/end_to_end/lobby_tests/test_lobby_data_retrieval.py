"""
Test lobby data retrieval functionality.
Following TDD approach - these tests will fail initially.
"""
import pytest
import requests
from tests.utils.test_data import generate_test_user, generate_test_group, generate_test_subject


class TestLobbyDataRetrieval:
    """Test retrieving lobby/session data via API"""
    
    def test_get_session_details_api(
        self, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login
    ):
        """GET /api/session/{session_id} liefert korrekte Lobby-Grunddaten"""
        # Create users
        host_username = "hostuser"
        host_password = "Test123!"
        host_email = "host@test.de"
        
        participant_username = "participantuser"
        participant_password = "Test123!"
        participant_email = "participant@test.de"
        
        # Setup
        api_create_user(host_username, host_email, host_password)
        api_create_user(participant_username, participant_email, participant_password)
        
        host_auth = api_login(host_username, host_password)
        participant_auth = api_login(participant_username, participant_password)
        
        group_name = "Biologie Gruppe"
        subject_name = "Genetik"
        
        group_data = api_create_group(group_name, host_auth)
        subject_data = api_create_subject(subject_name, group_name, host_auth)
        
        # Add participant to group
        response = requests.post(
            f"{server}/gruppe-beitreten",
            json={"gruppen_name": group_name},
            headers={"Authorization": participant_auth["Authorization"]},
            cookies=participant_auth.get('cookies')
        )
        assert response.status_code == 200
        
        # Create session
        response = requests.post(
            f"{server}/api/session/create",
            json={
                "subject_id": subject_data['id'],
                "group_id": group_data['id']
            },
            headers={"Authorization": host_auth["Authorization"]},
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        session_id = response.json()['session_id']
        join_code = response.json()['join_code']
        
        # Add participant to session
        response = requests.post(
            f"{server}/api/session/join",
            json={"join_code": join_code},
            headers={"Authorization": participant_auth["Authorization"]},
            cookies=participant_auth.get('cookies')
        )
        assert response.status_code == 200
        
        # Test GET endpoint
        response = requests.get(
            f"{server}/api/session/{session_id}",
            headers={"Authorization": host_auth["Authorization"]},
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify all required fields
        assert 'id' in data
        assert 'subject' in data
        assert 'group' in data
        assert 'host' in data
        assert 'participants' in data
        assert 'status' in data
        assert 'join_code' in data
        assert 'created_at' in data
        
        # Verify data content
        assert data['id'] == session_id
        assert data['subject']['name'] == subject_name
        assert data['subject']['id'] == subject_data['id']
        assert data['group']['name'] == group_name
        assert data['group']['id'] == group_data['id']
        assert data['host']['username'] == host_username
        assert data['status'] == 'waiting'
        assert data['join_code'] == join_code
        
        # Verify participants
        assert len(data['participants']) == 2
        participants_by_username = {p['username']: p for p in data['participants']}
        
        assert host_username in participants_by_username
        assert participants_by_username[host_username]['is_host'] is True
        
        assert participant_username in participants_by_username
        assert participants_by_username[participant_username]['is_host'] is False
    
    def test_get_session_unauthorized(
        self, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login
    ):
        """GET /api/session/{session_id} requires authentication"""
        # Create session
        user_data = generate_test_user()
        username = user_data['username']
        password = user_data['password']
        email = user_data['email']
        
        api_create_user(username, email, password)
        auth_data = api_login(username, password)
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        group_data = api_create_group(group_name, auth_data)
        subject_data = api_create_subject(subject_name, group_name, auth_data)
        
        response = requests.post(
            f"{server}/api/session/create",
            json={
                "subject_id": subject_data['id'],
                "group_id": group_data['id']
            },
            headers={"Authorization": auth_data["Authorization"]},
            cookies=auth_data.get('cookies')
        )
        assert response.status_code == 200
        session_id = response.json()['session_id']
        
        # Try to access without authentication
        response = requests.get(f"{server}/api/session/{session_id}")
        assert response.status_code == 401
    
    def test_get_session_not_found(
        self, server, clean_database,
        api_create_user, api_login
    ):
        """GET /api/session/{session_id} returns 404 for non-existent session"""
        user_data = generate_test_user()
        username = user_data['username']
        password = user_data['password']
        email = user_data['email']
        
        api_create_user(username, email, password)
        auth_data = api_login(username, password)
        
        # Try to access non-existent session
        fake_session_id = "12345678-1234-1234-1234-123456789012"
        response = requests.get(
            f"{server}/api/session/{fake_session_id}",
            headers={"Authorization": auth_data["Authorization"]},
            cookies=auth_data.get('cookies')
        )
        assert response.status_code == 404
        assert 'detail' in response.json()
    
    def test_get_session_includes_flashcard_count(
        self, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login
    ):
        """GET /api/session/{session_id} includes flashcard count for the subject"""
        username = "testuser"
        password = "Test123!"
        email = "test@test.de"
        group_name = "Test Group"
        subject_name = "Test Subject"
        
        api_create_user(username, email, password)
        auth_data = api_login(username, password)
        group_data = api_create_group(group_name, auth_data)
        subject_data = api_create_subject(subject_name, group_name, auth_data)
        
        # Create some flashcards
        for i in range(3):
            response = requests.post(
                f"{server}/flashcard/create",
                json={
                    "fach": subject_name,
                    "gruppe": group_name,
                    "frage": f"Test Question {i+1}",
                    "antworten": [
                        {"text": "Answer 1", "is_correct": True},
                        {"text": "Answer 2", "is_correct": False},
                        {"text": "Answer 3", "is_correct": False},
                        {"text": "Answer 4", "is_correct": False}
                    ]
                },
                headers={"Authorization": auth_data["Authorization"]},
                cookies=auth_data.get('cookies')
            )
            assert response.status_code == 200
        
        # Create session
        response = requests.post(
            f"{server}/api/session/create",
            json={
                "subject_id": subject_data['id'],
                "group_id": group_data['id']
            },
            headers={"Authorization": auth_data["Authorization"]},
            cookies=auth_data.get('cookies')
        )
        assert response.status_code == 200
        session_id = response.json()['session_id']
        
        # Get session details
        response = requests.get(
            f"{server}/api/session/{session_id}",
            headers={"Authorization": auth_data["Authorization"]},
            cookies=auth_data.get('cookies')
        )
        assert response.status_code == 200
        
        data = response.json()
        assert 'flashcard_count' in data
        assert data['flashcard_count'] == 3