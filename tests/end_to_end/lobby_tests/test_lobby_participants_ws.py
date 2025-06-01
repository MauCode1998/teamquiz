"""
Test WebSocket functionality for lobby participants.
Following TDD approach - these tests will fail initially.
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time
import json
import asyncio
import websockets
from tests.utils.test_data import generate_test_user, generate_test_group, generate_test_subject


class TestLobbyParticipantsWebSocket:
    """Test real-time participant updates via WebSocket"""
    
    def test_host_sees_self_in_lobby_via_websocket(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject,
        api_login, login_user_ui
    ):
        """Host sieht sich selbst in Lobby via WebSocket nach Join"""
        user_data = generate_test_user()
        username = user_data['username']
        password = user_data['password']
        email = user_data['email']
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        
        # Setup
        api_create_user(username, email, password)
        auth_data = api_login(username, password)
        group_data = api_create_group(group_name, auth_data)
        subject_data = api_create_subject(subject_name, group_name, auth_data)
        
        # Create session via API
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
        
        # Login via UI and navigate to lobby
        login_user_ui(username, password)
        driver.get(f"{server}/lobby/{session_id}")
        
        # Wait for WebSocket connection and participant list
        participant_list = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Teilnehmer')]"))
        )
        
        # Verify host sees themselves with host indicator
        host_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//li[contains(., '{username}') and contains(., '👑')]"))
        )
        assert host_element is not None
        
        # Verify participant count
        count_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Teilnehmer (1)')]"))
        )
        assert count_element is not None
    
    def test_multi_user_join_via_code_realtime_update(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject,
        api_login, login_user_ui, logout_user_ui
    ):
        """Zweiter User joint via Code, beide sehen sich (real-time Update für Host)"""
        # Create two users
        host_user = generate_test_user()
        host_username = host_user['username']
        host_password = host_user['password']
        host_email = host_user['email']
        
        participant_user = generate_test_user()
        participant_username = participant_user['username']
        participant_password = participant_user['password']
        participant_email = participant_user['email']
        
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        
        # Setup
        api_create_user(host_username, host_email, host_password)
        api_create_user(participant_username, participant_email, participant_password)
        
        host_auth = api_login(host_username, host_password)
        participant_auth = api_login(participant_username, participant_password)
        
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
        
        # Host creates session
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
        
        # Host joins lobby via UI
        login_user_ui(host_username, host_password)
        driver.get(f"{server}/lobby/{session_id}")
        
        # Verify host sees only themselves initially
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Teilnehmer (1)')]"))
        )
        
        # Store host's driver
        host_driver = driver
        
        # Create new driver for participant
        from selenium import webdriver
        participant_driver = webdriver.Safari() if driver.name == "Safari" else webdriver.Chrome()
        
        try:
            # Participant joins via join code
            participant_driver.get(server)
            
            # Login as participant
            username_field = WebDriverWait(participant_driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.send_keys(participant_username)
            
            password_field = participant_driver.find_element(By.NAME, "password")
            password_field.send_keys(participant_password)
            
            login_button = participant_driver.find_element(By.ID, "anmeldenButton")
            login_button.click()
            
            # Wait for login to complete
            WebDriverWait(participant_driver, 10).until(
                EC.url_contains("/groups")
            )
            
            # Navigate to join page and enter code
            participant_driver.get(f"{server}/join")
            
            code_input = WebDriverWait(participant_driver, 10).until(
                EC.presence_of_element_located((By.ID, "join-code-input"))
            )
            code_input.send_keys(join_code)
            
            join_button = participant_driver.find_element(By.ID, "join-session-button")
            join_button.click()
            
            # Wait for redirect to lobby
            WebDriverWait(participant_driver, 10).until(
                EC.url_contains(f"/lobby/{session_id}")
            )
            
            # Now verify both drivers see both participants
            # Host should see count update to 2
            WebDriverWait(host_driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Teilnehmer (2)')]"))
            )
            
            # Host should see participant
            host_sees_participant = WebDriverWait(host_driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//li[contains(., '{participant_username}')]"))
            )
            assert host_sees_participant is not None
            
            # Participant should see both users
            participant_sees_count = WebDriverWait(participant_driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Teilnehmer (2)')]"))
            )
            assert participant_sees_count is not None
            
            participant_sees_host = WebDriverWait(participant_driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//li[contains(., '{host_username}') and contains(., '👑')]"))
            )
            assert participant_sees_host is not None
            
        finally:
            participant_driver.quit()
    
    def test_realtime_updates_on_user_leave(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject,
        api_login, login_user_ui
    ):
        """Real-time Updates bei Leave eines Users"""
        # Create three users
        users = []
        for i in range(3):
            user_data = generate_test_user()
            users.append(user_data)
            api_create_user(user_data['username'], user_data['email'], user_data['password'])
        
        # Setup group and subject
        host_auth = api_login(users[0]['username'], users[0]['password'])
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        group_data = api_create_group(group_name, host_auth)
        subject_data = api_create_subject(subject_name, group_name, host_auth)
        
        # Add other users to group
        for user in users[1:]:
            auth = api_login(user['username'], user['password'])
            response = requests.post(
                f"{server}/gruppe-beitreten",
                json={"gruppen_name": group_name},
                headers={"Authorization": auth["Authorization"]},
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
            headers={"Authorization": host_auth["Authorization"]},
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        session_id = response.json()['session_id']
        join_code = response.json()['join_code']
        
        # All users join via API first
        for user in users[1:]:
            auth = api_login(user['username'], user['password'])
            response = requests.post(
                f"{server}/api/session/join",
                json={"join_code": join_code},
                headers={"Authorization": auth["Authorization"]},
                cookies=auth.get('cookies')
            )
            assert response.status_code == 200
        
        # Host joins lobby via UI
        login_user_ui(users[0]['username'], users[0]['password'])
        driver.get(f"{server}/lobby/{session_id}")
        
        # Verify all 3 users are shown
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Teilnehmer (3)')]"))
        )
        
        # User 2 leaves the lobby via API
        auth_user2 = api_login(users[1]['username'], users[1]['password'])
        response = requests.post(
            f"{server}/api/session/leave/{session_id}",
            headers={"Authorization": auth_user2["Authorization"]},
            cookies=auth_user2.get('cookies')
        )
        assert response.status_code == 200
        
        # Verify count updates to 2 in real-time
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Teilnehmer (2)')]"))
        )
        
        # Verify user1 is no longer in the list
        # Wait for element to disappear
        WebDriverWait(driver, 10).until_not(
            EC.presence_of_element_located((By.XPATH, f"//li[contains(., '{users[1]['username']}')]"))
        )
    
    def test_websocket_lobby_update_message_format(
        self, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login
    ):
        """WebSocket lobby_update enthält korrekte Teilnehmerdaten (keine Mocks)"""
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
            headers={"Authorization": auth_data["Authorization"]},
            cookies=auth_data.get('cookies')
        )
        assert response.status_code == 200
        session_id = response.json()['session_id']
        ws_url = response.json()['websocket_url']
        
        # Extract token from cookies
        token = auth_data['cookies'].get('access_token')
        if token and token.startswith('Bearer '):
            token = token[7:]
        
        # Test WebSocket connection and messages
        async def test_websocket():
            uri = ws_url.replace('{token}', token)
            async with websockets.connect(uri) as websocket:
                # Send join_lobby message
                await websocket.send(json.dumps({
                    "type": "join_lobby",
                    "session_id": session_id
                }))
                
                # Receive lobby_update message
                message = await websocket.recv()
                data = json.loads(message)
                
                # Verify message format
                assert data['type'] == 'lobby_update'
                assert data['session_id'] == session_id
                assert 'participants' in data
                assert 'status' in data
                
                # Verify participants data
                assert len(data['participants']) == 1
                participant = data['participants'][0]
                assert participant['user_id'] > 0
                assert participant['username'] == username
                assert participant['is_host'] is True
                
                # Verify no mock data
                assert participant['username'] != 'Mock User'
                assert participant['username'] != 'Test User'
                
                # Verify status
                assert data['status'] == 'waiting'
        
        # Run async test
        asyncio.run(test_websocket())