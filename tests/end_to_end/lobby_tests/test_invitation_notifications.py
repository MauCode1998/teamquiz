"""
Test invitation notification functionality.
Following TDD approach - these tests will fail initially.
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time
from tests.utils.test_data import generate_test_user, generate_test_group, generate_test_subject


class TestInvitationNotifications:
    """Test notification badge and updates for invitations"""
    
    def test_notification_badge_shows_count(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject,
        api_login, login_user_ui
    ):
        """Badge zeigt Anzahl korrekt an"""
        # Create users
        invitee_user = generate_test_user()
        invitee_username = invitee_user['username']
        invitee_password = invitee_user['password']
        invitee_email = invitee_user['email']
        
        api_create_user(invitee_username, invitee_email, invitee_password)
        invitee_auth = api_login(invitee_username, invitee_password)
        
        # Create 3 hosts who will invite the user
        sessions = []
        for i in range(3):
            host_user = generate_test_user()
            host_username = host_user['username']
            host_email = host_user['email']
            host_password = host_user['password']
            
            api_create_user(host_username, host_email, host_password)
            host_auth = api_login(host_username, host_password)
            
            group_name = generate_test_group()
            subject_name = generate_test_subject()
            
            group_data = api_create_group(group_name, host_auth)
            subject_data = api_create_subject(subject_name, group_name, host_auth)
            
            # Add invitee to group
            response = requests.post(
                f"{server}/gruppe-beitreten",
                json={"gruppen_name": group_name},
                cookies=invitee_auth.get('cookies')
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
            
            # Send invitation
            response = requests.post(
                f"{server}/api/invitation/send",
                json={
                    "session_id": session_id,
                    "invitee_username": invitee_username
                },
                cookies=host_auth.get('cookies')
            )
            assert response.status_code == 200
            
            sessions.append({
                'session_id': session_id,
                'invitation_id': response.json()['invitation_id'],
                'host': host_username,
                'subject': subject_name
            })
        
        # Login as invitee
        login_user_ui(invitee_username, invitee_password)
        
        # Navigate to groups page (where header is visible)
        driver.get(f"{server}/groups")
        
        # Check notification badge shows "3"
        badge = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "notification-badge"))
        )
        assert badge.text == "3"
        
        # Verify badge is visible
        assert badge.is_displayed()
        
        # Click notification icon to verify dropdown content
        notification_icon = driver.find_element(By.ID, "notification-icon")
        notification_icon.click()
        
        # Verify dropdown shows 3 invitations
        invitation_items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "invitation-item"))
        )
        assert len(invitation_items) == 3
    
    def test_badge_updates_after_accept(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject,
        api_login, login_user_ui
    ):
        """Badge updated nach Accept"""
        # Create users
        host_user = generate_test_user()
        invitee_user = generate_test_user()
        host_username = host_user['username']
        invitee_username = invitee_user['username']
        password = host_user['password']
        
        api_create_user(host_username, host_user['email'], password)
        api_create_user(invitee_username, invitee_user['email'], password)
        
        host_auth = api_login(host_username, password)
        invitee_auth = api_login(invitee_username, password)
        
        # Create 2 sessions and send invitations
        invitation_ids = []
        for i in range(2):
            group_name = generate_test_group()
            subject_name = generate_test_subject()
            
            group_data = api_create_group(group_name, host_auth)
            subject_data = api_create_subject(subject_name, group_name, host_auth)
            
            # Add invitee to group
            response = requests.post(
                f"{server}/gruppe-beitreten",
                json={"gruppen_name": group_name},
                cookies=invitee_auth.get('cookies')
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
            
            # Send invitation
            response = requests.post(
                f"{server}/api/invitation/send",
                json={
                    "session_id": response.json()['session_id'],
                    "invitee_username": invitee_username
                },
                cookies=host_auth.get('cookies')
            )
            assert response.status_code == 200
            invitation_ids.append(response.json()['invitation_id'])
        
        # Login as invitee
        login_user_ui(invitee_username, password)
        driver.get(f"{server}/groups")
        
        # Verify badge shows "2"
        badge = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "notification-badge"))
        )
        assert badge.text == "2"
        
        # Open dropdown and accept first invitation
        notification_icon = driver.find_element(By.ID, "notification-icon")
        notification_icon.click()
        
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//button[@data-invitation-id='{invitation_ids[0]}' and contains(@class, 'accept')]"))
        )
        accept_button.click()
        
        # Wait for badge to update to "1"
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.ID, "notification-badge").text == "1"
        )
        
        # Verify badge now shows "1"
        badge = driver.find_element(By.ID, "notification-badge")
        assert badge.text == "1"
    
    def test_badge_updates_after_reject(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject,
        api_login, login_user_ui
    ):
        """Badge updated nach Reject"""
        # Similar to accept test but with reject
        host_user = generate_test_user()
        invitee_user = generate_test_user()
        host_username = host_user['username']
        invitee_username = invitee_user['username']
        password = host_user['password']
        
        api_create_user(host_username, host_user['email'], password)
        api_create_user(invitee_username, invitee_user['email'], password)
        
        host_auth = api_login(host_username, password)
        invitee_auth = api_login(invitee_username, password)
        
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        group_data = api_create_group(group_name, host_auth)
        subject_data = api_create_subject(subject_name, group_name, host_auth)
        
        # Add invitee to group
        response = requests.post(
            f"{server}/gruppe-beitreten",
            json={"gruppen_name": group_name},
            cookies=invitee_auth.get('cookies')
        )
        assert response.status_code == 200
        
        # Create session and send invitation
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
        
        response = requests.post(
            f"{server}/api/invitation/send",
            json={
                "session_id": session_id,
                "invitee_username": invitee_username
            },
            cookies=host_auth.get('cookies')
        )
        assert response.status_code == 200
        invitation_id = response.json()['invitation_id']
        
        # Login as invitee
        login_user_ui(invitee_username, password)
        driver.get(f"{server}/groups")
        
        # Verify badge shows "1"
        badge = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "notification-badge"))
        )
        assert badge.text == "1"
        
        # Open dropdown and reject invitation
        notification_icon = driver.find_element(By.ID, "notification-icon")
        notification_icon.click()
        
        reject_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//button[@data-invitation-id='{invitation_id}' and contains(@class, 'reject')]"))
        )
        reject_button.click()
        
        # Wait for badge to disappear (no pending invitations)
        WebDriverWait(driver, 10).until_not(
            EC.presence_of_element_located((By.ID, "notification-badge"))
        )
        
        # Verify dropdown shows no invitations
        empty_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Keine Einladungen')]"))
        )
        assert empty_message is not None
    
    def test_multiple_invitations_aggregated(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject,
        api_login, login_user_ui
    ):
        """Multiple Einladungen korrekt aggregiert"""
        invitee_user = generate_test_user()
        invitee_username = invitee_user['username']
        invitee_password = invitee_user['password']
        invitee_email = invitee_user['email']
        
        api_create_user(invitee_username, invitee_email, invitee_password)
        invitee_auth = api_login(invitee_username, invitee_password)
        
        # Create 5 different hosts sending invitations
        all_invitations = []
        
        for i in range(5):
            host_user = generate_test_user()
            host_username = host_user['username']
            host_email = host_user['email']
            host_password = host_user['password']
            
            api_create_user(host_username, host_email, host_password)
            host_auth = api_login(host_username, host_password)
            
            group_name = generate_test_group()
            subject_name = generate_test_subject()
            
            group_data = api_create_group(group_name, host_auth)
            subject_data = api_create_subject(subject_name, group_name, host_auth)
            
            # Add invitee to group
            response = requests.post(
                f"{server}/gruppe-beitreten",
                json={"gruppen_name": group_name},
                cookies=invitee_auth.get('cookies')
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
            
            # Send invitation
            response = requests.post(
                f"{server}/api/invitation/send",
                json={
                    "session_id": session_id,
                    "invitee_username": invitee_username
                },
                cookies=host_auth.get('cookies')
            )
            assert response.status_code == 200
            
            all_invitations.append({
                'invitation_id': response.json()['invitation_id'],
                'host': host_username,
                'subject': subject_name
            })
        
        # Login as invitee
        login_user_ui(invitee_username, invitee_password)
        driver.get(f"{server}/groups")
        
        # Verify badge shows "5"
        badge = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "notification-badge"))
        )
        assert badge.text == "5"
        
        # Open dropdown
        notification_icon = driver.find_element(By.ID, "notification-icon")
        notification_icon.click()
        
        # Verify all 5 invitations are shown
        invitation_items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "invitation-item"))
        )
        assert len(invitation_items) == 5
        
        # Verify each invitation shows correct host and subject
        for invitation in all_invitations:
            invitation_text = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//div[@class='invitation-item' and contains(., '{invitation['host']}') and contains(., '{invitation['subject']}')]"))
            )
            assert invitation_text is not None
        
        # Accept 2 invitations
        for i in range(2):
            accept_button = driver.find_element(
                By.XPATH, 
                f"//button[@data-invitation-id='{all_invitations[i]['invitation_id']}' and contains(@class, 'accept')]"
            )
            accept_button.click()
            time.sleep(0.5)  # Small delay to ensure update
        
        # Verify badge updates to "3"
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.ID, "notification-badge").text == "3"
        )
        
        badge = driver.find_element(By.ID, "notification-badge")
        assert badge.text == "3"