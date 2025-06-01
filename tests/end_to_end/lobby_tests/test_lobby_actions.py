"""
Test lobby actions (start quiz, leave lobby).
Following TDD approach - these tests will fail initially.
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time
from tests.utils.test_data import generate_test_user, generate_test_group, generate_test_subject


class TestLobbyActions:
    """Test actions that can be performed in the lobby"""
    
    def test_quiz_start_only_for_host(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject,
        api_login, login_user_ui, logout_user_ui
    ):
        """'Quiz starten' nur für Host möglich (API-Schutz, WS-Status-Update)"""
        # Create host and participant
        host_user = generate_test_user()
        participant_user = generate_test_user()
        host_username = host_user['username']
        participant_username = participant_user['username']
        password = host_user['password']
        
        api_create_user(host_username, host_user['email'], password)
        api_create_user(participant_username, participant_user['email'], password)
        
        host_auth = api_login(host_username, password)
        participant_auth = api_login(participant_username, password)
        
        # Setup
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        group_data = api_create_group(group_name, host_auth)
        subject_data = api_create_subject(subject_name, group_name, host_auth)
        
        # Add participant to group
        response = requests.post(
            f"{server}/gruppe-beitreten",
            json={"gruppen_name": group_name},
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
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        session_id = response.json()['session_id']
        join_code = response.json()['join_code']
        
        # Participant joins
        response = requests.post(
            f"{server}/api/session/join",
            json={"join_code": join_code},
            cookies=participant_auth.get('cookies')
        )
        assert response.status_code == 200
        
        # Test 1: Host sees "Quiz starten" button
        login_user_ui(host_username, password)
        driver.get(f"{server}/lobby/{session_id}")
        
        start_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "start-quiz-button"))
        )
        assert start_button is not None
        assert start_button.is_displayed()
        assert start_button.is_enabled()
        
        logout_user_ui()
        
        # Test 2: Participant does NOT see "Quiz starten" button
        login_user_ui(participant_username, password)
        driver.get(f"{server}/lobby/{session_id}")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Teilnehmer')]"))
        )
        
        # Verify no start button for participant
        start_buttons = driver.find_elements(By.ID, "start-quiz-button")
        assert len(start_buttons) == 0, "Participant should not see start button"
        
        # Test 3: API protection - participant cannot start via API
        response = requests.post(
            f"{server}/api/session/start/{session_id}",
            cookies=participant_auth.get('cookies')
        )
        assert response.status_code == 403, "Non-host should get 403 Forbidden"
        assert 'only host' in response.json()['detail'].lower()
        
        # Test 4: Host can start via API
        response = requests.post(
            f"{server}/api/session/start/{session_id}",
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        assert response.json()['status'] == 'starting' or response.json()['status'] == 'in_progress'
        
        # Verify status change via WebSocket update (check in UI)
        status_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Quiz wird gestartet')]"))
        )
        assert status_element is not None
    
    def test_leave_lobby_removes_participant(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject,
        api_login, login_user_ui
    ):
        """'Lobby verlassen' entfernt Teilnehmer, triggert WS-Update"""
        # Create users
        host_user = generate_test_user()
        participant1_user = generate_test_user()
        participant2_user = generate_test_user()
        host_username = host_user['username']
        participant1_username = participant1_user['username']
        participant2_username = participant2_user['username']
        password = host_user['password']
        
        api_create_user(host_username, host_user['email'], password)
        api_create_user(participant1_username, participant1_user['email'], password)
        api_create_user(participant2_username, participant2_user['email'], password)
        
        host_auth = api_login(host_username, password)
        p1_auth = api_login(participant1_username, password)
        p2_auth = api_login(participant2_username, password)
        
        # Setup
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        group_data = api_create_group(group_name, host_auth)
        subject_data = api_create_subject(subject_name, group_name, host_auth)
        
        # Add participants to group
        for auth in [p1_auth, p2_auth]:
            response = requests.post(
                f"{server}/gruppe-beitreten",
                json={"gruppen_name": group_name},
                cookies=auth.get('cookies')
            )
            assert response.status_code == 200
        
        # Create session
        response = requests.post(
            f"{server}/api/session/create",
            json={
                "subject_id": subject_data['id'],
                "group_id": group_data['id']
            },
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        session_id = response.json()['session_id']
        join_code = response.json()['join_code']
        
        # Both participants join
        for auth in [p1_auth, p2_auth]:
            response = requests.post(
                f"{server}/api/session/join",
                json={"join_code": join_code},
                cookies=auth.get('cookies')
            )
            assert response.status_code == 200
        
        # Login as host to watch updates
        login_user_ui(host_username, password)
        driver.get(f"{server}/lobby/{session_id}")
        
        # Verify 3 participants initially
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Teilnehmer (3)')]"))
        )
        
        # Participant 1 leaves via API
        response = requests.post(
            f"{server}/api/session/leave/{session_id}",
            cookies=p1_auth.get('cookies')
        )
        assert response.status_code == 200
        
        # Verify count updates to 2 in real-time
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Teilnehmer (2)')]"))
        )
        
        # Verify participant1 is no longer in list
        WebDriverWait(driver, 10).until_not(
            EC.presence_of_element_located((By.XPATH, f"//li[contains(., '{participant1_username}')]"))
        )
        
        # Verify via API
        response = requests.get(
            f"{server}/api/session/{session_id}",
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        
        participants = response.json()['participants']
        participant_usernames = [p['username'] for p in participants]
        assert participant1_username not in participant_usernames
        assert participant2_username in participant_usernames
        assert host_username in participant_usernames
        assert len(participants) == 2
    
    def test_leave_lobby_button_in_ui(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject,
        api_login, login_user_ui
    ):
        """'Lobby verlassen' Button in UI funktioniert"""
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
        
        # Create session
        response = requests.post(
            f"{server}/api/session/create",
            json={
                "subject_id": subject_data['id'],
                "group_id": group_data['id']
            },
            cookies=auth_data.get('cookies')
        )
        assert response.status_code == 200
        session_id = response.json()['session_id']
        
        # Navigate to lobby
        login_user_ui(username, password)
        driver.get(f"{server}/lobby/{session_id}")
        
        # Find and click leave button
        leave_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "leave-lobby-button"))
        )
        leave_button.click()
        
        # Verify redirect away from lobby (to groups page)
        WebDriverWait(driver, 10).until(
            EC.url_contains("/groups")
        )
        
        # Verify user is no longer in session via API
        response = requests.get(
            f"{server}/api/session/{session_id}",
            cookies=auth_data.get('cookies')
        )
        # Should either be 404 (session deleted if empty) or user not in participants
        if response.status_code == 200:
            participants = response.json()['participants']
            participant_usernames = [p['username'] for p in participants]
            assert username not in participant_usernames
    
    def test_host_transfer_when_host_leaves(
        self, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login
    ):
        """Wenn Host geht, ältester Teilnehmer wird neuer Host"""
        # Create users
        host_user = generate_test_user()
        p1_user = generate_test_user()
        p2_user = generate_test_user()
        host_username = host_user['username']
        p1_username = p1_user['username']
        p2_username = p2_user['username']
        password = host_user['password']
        
        api_create_user(host_username, host_user['email'], password)
        api_create_user(p1_username, p1_user['email'], password)
        api_create_user(p2_username, p2_user['email'], password)
        
        host_auth = api_login(host_username, password)
        p1_auth = api_login(p1_username, password)
        p2_auth = api_login(p2_username, password)
        
        # Setup
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        group_data = api_create_group(group_name, host_auth)
        subject_data = api_create_subject(subject_name, group_name, host_auth)
        
        # Add participants to group
        for auth in [p1_auth, p2_auth]:
            response = requests.post(
                f"{server}/gruppe-beitreten",
                json={"gruppen_name": group_name},
                cookies=auth.get('cookies')
            )
            assert response.status_code == 200
        
        # Create session
        response = requests.post(
            f"{server}/api/session/create",
            json={
                "subject_id": subject_data['id'],
                "group_id": group_data['id']
            },
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        session_id = response.json()['session_id']
        join_code = response.json()['join_code']
        
        # Participants join in order (p1 first, then p2)
        time.sleep(0.5)  # Ensure join order
        response = requests.post(
            f"{server}/api/session/join",
            json={"join_code": join_code},
            cookies=p1_auth.get('cookies')
        )
        assert response.status_code == 200
        
        time.sleep(0.5)  # Ensure join order
        response = requests.post(
            f"{server}/api/session/join",
            json={"join_code": join_code},
            cookies=p2_auth.get('cookies')
        )
        assert response.status_code == 200
        
        # Verify initial state
        response = requests.get(
            f"{server}/api/session/{session_id}",
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        assert response.json()['host']['username'] == host_username
        
        # Original host leaves
        response = requests.post(
            f"{server}/api/session/leave/{session_id}",
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        
        # Check new host (should be p1 as they joined first)
        response = requests.get(
            f"{server}/api/session/{session_id}",
            cookies=p1_auth.get('cookies')
        )
        assert response.status_code == 200
        
        session_data = response.json()
        assert session_data['host']['username'] == p1_username
        
        # Verify p1 is marked as host in participants
        p1_participant = next(p for p in session_data['participants'] if p['username'] == p1_username)
        assert p1_participant['is_host'] is True
        
        # Verify p2 is not host
        p2_participant = next(p for p in session_data['participants'] if p['username'] == p2_username)
        assert p2_participant['is_host'] is False