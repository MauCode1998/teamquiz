"""
Test invitation system functionality.
Following TDD approach - these tests will fail initially.
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time
from tests.utils.test_data import generate_test_user, generate_test_group, generate_test_subject


class TestInvitationSystem:
    """Test sending, receiving, and managing invitations"""
    
    def test_send_invitation_success(
        self, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login
    ):
        """Einladung senden (erfolgreich, DB-Eintrag)"""
        # Create users
        host_user = generate_test_user("host")
        invitee_user = generate_test_user("invitee")
        
        api_create_user(host_user["username"], host_user["email"], host_user["password"])
        api_create_user(invitee_user["username"], invitee_user["email"], invitee_user["password"])
        
        host_auth = api_login(host_user["username"], host_user["password"])
        invitee_auth = api_login(invitee_user["username"], invitee_user["password"])
        
        # Setup group and subject
        group_data = api_create_group("Invite Test Group", host_auth)
        subject_data = api_create_subject("Invite Subject", "Invite Test Group", host_auth)
        
        # Add invitee to group (required for invitation)
        response = requests.post(
            f"{server}/gruppe-beitreten",
            json={"gruppen_name": "Invite Test Group"},
            headers={"Authorization": invitee_auth["Authorization"]},
            cookies=invitee_auth.get('cookies')
        )
        assert response.status_code == 200
        
        # Create session
        response = requests.post(
            f"{server}/api/session/create",
            json={
                "subject_name": "Invite Subject",
                "group_name": "Invite Test Group"
            },
            headers={"Authorization": host_auth["Authorization"]},
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        session_id = response.json()['session_id']
        
        # Send invitation
        response = requests.post(
            f"{server}/api/invitation/send",
            json={
                "session_id": session_id,
                "invitee_username": invitee_user["username"]
            },
            headers={"Authorization": host_auth["Authorization"]},
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        
        data = response.json()
        assert 'invitation_id' in data
        assert data['status'] == 'sent'
        
        # Verify invitation in invitee's pending list
        response = requests.get(
            f"{server}/api/invitations/pending",
            headers={"Authorization": invitee_auth["Authorization"]},
            cookies=invitee_auth.get('cookies')
        )
        assert response.status_code == 200
        
        invitations = response.json()
        assert len(invitations) == 1
        assert invitations[0]['invitation_id'] == data['invitation_id']
        assert invitations[0]['inviter'] == host_user["username"]
        assert invitations[0]['subject'] == "Invite Subject"
    
    def test_send_invitation_to_nonexistent_user(
        self, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login
    ):
        """Einladung senden an nicht-existenten User (Fehler)"""
        user_data = generate_test_user()
        username = user_data['username']
        password = user_data['password']
        
        api_create_user(username, user_data['email'], password)
        auth_data = api_login(username, password)
        
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        group_data = api_create_group(group_name, auth_data)
        subject_data = api_create_subject(subject_name, group_name, auth_data)
        
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
        
        # Try to invite non-existent user
        response = requests.post(
            f"{server}/api/invitation/send",
            json={
                "session_id": session_id,
                "invitee_username": "ghostuser12345"
            },
            headers={"Authorization": auth_data["Authorization"]},
            cookies=auth_data.get('cookies')
        )
        assert response.status_code == 404
        assert 'detail' in response.json()
    
    def test_send_invitation_to_user_already_in_lobby(
        self, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login
    ):
        """Einladung senden an User bereits in Lobby (Fehler)"""
        host_user = generate_test_user()
        participant_user = generate_test_user()
        host_username = host_user['username']
        participant_username = participant_user['username']
        password = host_user['password']
        
        api_create_user(host_username, host_user['email'], password)
        api_create_user(participant_username, participant_user['email'], password)
        
        host_auth = api_login(host_username, password)
        participant_auth = api_login(participant_username, password)
        
        group_name = generate_test_group()
        subject_name = generate_test_subject()
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
                "subject_name": "Invite Subject",
                "group_name": "Invite Test Group"
            },
            headers={"Authorization": host_auth["Authorization"]},
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        session_id = response.json()['session_id']
        join_code = response.json()['join_code']
        
        # Participant joins session
        response = requests.post(
            f"{server}/api/session/join",
            json={"join_code": join_code},
            headers={"Authorization": participant_auth["Authorization"]},
            cookies=participant_auth.get('cookies')
        )
        assert response.status_code == 200
        
        # Try to invite participant who is already in lobby
        response = requests.post(
            f"{server}/api/invitation/send",
            json={
                "session_id": session_id,
                "invitee_username": participant_username
            },
            headers={"Authorization": host_auth["Authorization"]},
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 400
        assert 'already in lobby' in response.json()['detail'].lower()
    
    def test_no_self_invitation_button(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject,
        api_login, login_user_ui
    ):
        """Kein Einladen-Button beim eigenen Namen in Teilnehmerliste"""
        username = "testuser"
        password = "Test123!"
        email = "test@test.de"
        
        api_create_user(username, email, password)
        auth_data = api_login(username, password)
        group_data = api_create_group("Self Invite Test", auth_data)
        subject_data = api_create_subject("Test Subject", "Self Invite Test", auth_data)
        
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
        
        # Login and navigate to lobby
        login_user_ui(username, password)
        driver.get(f"{server}/lobby/{session_id}")
        
        # Wait for participant list
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//li[contains(., '{username}')]"))
        )
        
        # Verify no invite button next to own name
        user_element = driver.find_element(By.XPATH, f"//li[contains(., '{username}')]")
        
        # Check that there's no invite button within this element
        invite_buttons = user_element.find_elements(By.XPATH, ".//button[contains(text(), 'Einladen')]")
        assert len(invite_buttons) == 0, "Should not have invite button next to own name"
    
    def test_accept_invitation_flow(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject,
        api_login, login_user_ui, logout_user_ui
    ):
        """Einladung annehmen (User wird Teilnehmer, Redirect, WS-Update)"""
        host_username = "hostanna"
        invitee_username = "inviteemax"
        password = "Test123!"
        
        api_create_user(host_username, "host@test.de", password)
        api_create_user(invitee_username, "invitee@test.de", password)
        
        host_auth = api_login(host_username, password)
        invitee_auth = api_login(invitee_username, password)
        
        group_data = api_create_group("Accept Test Group", host_auth)
        subject_data = api_create_subject("Accept Subject", "Accept Test Group", host_auth)
        
        # Add invitee to group
        response = requests.post(
            f"{server}/gruppe-beitreten",
            json={"gruppen_name": "Accept Test Group"},
            headers={"Authorization": invitee_auth["Authorization"]},
            cookies=invitee_auth.get('cookies')
        )
        assert response.status_code == 200
        
        # Create session
        response = requests.post(
            f"{server}/api/session/create",
            json={
                "subject_name": "Invite Subject",
                "group_name": "Invite Test Group"
            },
            headers={"Authorization": host_auth["Authorization"]},
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        session_id = response.json()['session_id']
        
        # Send invitation
        response = requests.post(
            f"{server}/api/invitation/send",
            json={
                "session_id": session_id,
                "invitee_username": invitee_user["username"]
            },
            headers={"Authorization": host_auth["Authorization"]},
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        invitation_id = response.json()['invitation_id']
        
        # Login as invitee
        login_user_ui(invitee_username, password)
        
        # Click notification icon in header
        notification_icon = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "notification-icon"))
        )
        notification_icon.click()
        
        # Wait for dropdown to appear
        dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "invitation-dropdown"))
        )
        
        # Find and click accept button
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//button[@data-invitation-id='{invitation_id}' and contains(@class, 'accept')]"))
        )
        accept_button.click()
        
        # Verify redirect to lobby
        WebDriverWait(driver, 10).until(
            EC.url_contains(f"/lobby/{session_id}")
        )
        
        # Verify user is in participant list
        participant_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//li[contains(., '{invitee_username}')]"))
        )
        assert participant_element is not None
        
        # Verify via API that user is participant
        response = requests.get(
            f"{server}/api/session/{session_id}",
            headers={"Authorization": invitee_auth["Authorization"]},
            cookies=invitee_auth.get('cookies')
        )
        assert response.status_code == 200
        
        participants = response.json()['participants']
        participant_usernames = [p['username'] for p in participants]
        assert invitee_username in participant_usernames
    
    def test_reject_invitation_flow(
        self, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login
    ):
        """Einladung ablehnen (Status-Update in DB)"""
        host_user = generate_test_user()
        invitee_user = generate_test_user()
        host_username = host_user['username']
        invitee_username = invitee_user['username']
        password = host_user['password']
        
        api_create_user(host_username, host_user['email'], password)
        api_create_user(invitee_username, invitee_user['email'], invitee_user['password'])
        
        host_auth = api_login(host_username, password)
        invitee_auth = api_login(invitee_username, invitee_user['password'])
        
        group_data = api_create_group("Reject Test Group", host_auth)
        subject_data = api_create_subject("Reject Subject", "Reject Test Group", host_auth)
        
        # Add invitee to group
        response = requests.post(
            f"{server}/gruppe-beitreten",
            json={"gruppen_name": "Reject Test Group"},
            headers={"Authorization": invitee_auth["Authorization"]},
            cookies=invitee_auth.get('cookies')
        )
        assert response.status_code == 200
        
        # Create session
        response = requests.post(
            f"{server}/api/session/create",
            json={
                "subject_name": "Invite Subject",
                "group_name": "Invite Test Group"
            },
            headers={"Authorization": host_auth["Authorization"]},
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        session_id = response.json()['session_id']
        
        # Send invitation
        response = requests.post(
            f"{server}/api/invitation/send",
            json={
                "session_id": session_id,
                "invitee_username": invitee_username
            },
            headers={"Authorization": host_auth["Authorization"]},
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        invitation_id = response.json()['invitation_id']
        
        # Reject invitation
        response = requests.post(
            f"{server}/api/invitation/reject/{invitation_id}",
            headers={"Authorization": invitee_auth["Authorization"]},
            cookies=invitee_auth.get('cookies')
        )
        assert response.status_code == 200
        assert response.json()['status'] == 'rejected'
        
        # Verify invitation no longer in pending list
        response = requests.get(
            f"{server}/api/invitations/pending",
            headers={"Authorization": invitee_auth["Authorization"]},
            cookies=invitee_auth.get('cookies')
        )
        assert response.status_code == 200
        assert len(response.json()) == 0
        
        # Verify user is not in session participants
        response = requests.get(
            f"{server}/api/session/{session_id}",
            headers={"Authorization": host_auth["Authorization"]},
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        
        participants = response.json()['participants']
        participant_usernames = [p['username'] for p in participants]
        assert invitee_username not in participant_usernames