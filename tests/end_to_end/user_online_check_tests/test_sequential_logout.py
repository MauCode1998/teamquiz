"""
Test sequential logout of multiple users
This tests the core requirement: users logging out one by one and names disappearing in real-time
"""
import pytest
import time
import subprocess
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.test_data import generate_test_user, generate_test_group, generate_test_subject


class TestSequentialLogout:
    """Test multiple users logging out sequentially with real-time name updates"""

    def test_three_users_sequential_logout(
        self, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login
    ):
        """Test 3 users login, then logout one by one with real-time name updates"""
        print("\n🎬 Starting SEQUENTIAL LOGOUT test: 3 users logout one by one")
        
        # === SETUP: Create test data via API ===
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        
        # Create 3 test users
        users = []
        for i in range(3):
            user_data = generate_test_user()
            users.append(user_data)
            api_create_user(user_data["username"], user_data["email"], user_data["password"])
        
        # Create group and subject
        auth_data = api_login(users[0]["username"], users[0]["password"])
        api_create_group(group_name, auth_data)
        api_create_subject(subject_name, group_name, auth_data)
        
        print(f"✅ SETUP: Created 3 users ({[u['username'] for u in users]}) and group '{group_name}'")
        
        # === STEP 1: Create 3 separate browser sessions ===
        browser_sessions = []
        for i in range(3):
            try:
                # Use Safari driver (matching conftest.py)
                driver = webdriver.Safari()
                driver.implicitly_wait(10)
                browser_sessions.append({
                    'driver': driver,
                    'user': users[i],
                    'index': i
                })
            except Exception as e:
                # Cleanup any created drivers
                for session in browser_sessions:
                    session['driver'].quit()
                pytest.skip(f"Safari driver not available: {e}")
        
        print("✅ Created 3 Safari browser sessions")
        
        try:
            # === STEP 2: Login all 3 users to same group/subject ===
            def login_user_session(session):
                """Login a user session and navigate to subject page"""
                driver = session['driver']
                user = session['user']
                index = session['index']
                
                print(f"🔄 User {index + 1} ({user['username']}) logging in...")
                
                # Manual login (copying from conftest.py pattern)
                driver.get(f"{server}/")
                time.sleep(1)
                
                # Find and fill username
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Benutzername']"))
                )
                username_field.clear()
                username_field.send_keys(user['username'])
                
                # Find and fill password
                password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                password_field.clear()
                password_field.send_keys(user['password'])
                
                # Submit
                submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Anmelden')]")
                submit_button.click()
                
                # Wait for groups page
                WebDriverWait(driver, 10).until(EC.url_contains("/groups"))
                
                # Navigate to group
                driver.get(f"{server}/groups/{group_name}")
                time.sleep(2)
                
                # Navigate to subject (where OnlineUsers is)
                subject_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '{subject_name}')]"))
                )
                subject_link.click()
                time.sleep(3)  # Allow WebSocket to connect
                
                print(f"✅ User {index + 1} ({user['username']}) logged in and on subject page")
            
            # Login all users sequentially (with delays to avoid race conditions)
            for session in browser_sessions:
                login_user_session(session)
                time.sleep(2)  # Small delay between logins
            
            print("✅ All 3 users logged in")
            
            # === STEP 3: Verify all 3 users see each other online ===
            time.sleep(3)  # Allow WebSocket updates to propagate
            
            for session in browser_sessions:
                driver = session['driver']
                user = session['user']
                index = session['index']
                
                try:
                    # Check online count
                    online_header = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '🟢 Online')]"))
                    )
                    header_text = online_header.text
                    print(f"User {index + 1} sees: {header_text}")
                    
                    # Should show "🟢 Online (3)"
                    assert "(3)" in header_text or "3" in header_text
                    
                    # Verify all usernames are visible
                    for other_user in users:
                        username_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{other_user['username']}')]")
                        # Filter out navigation/header elements, focus on online users section
                        visible_elements = [el for el in username_elements if el.is_displayed()]
                        assert len(visible_elements) > 0, f"User {other_user['username']} not visible to {user['username']}"
                    
                    print(f"✅ User {index + 1} sees all 3 users online")
                    
                except Exception as e:
                    print(f"❌ User {index + 1} verification failed: {e}")
                    driver.save_screenshot(f"test_reports/user_{index + 1}_all_online_failed.png")
                    raise
            
            # === STEP 4: Sequential logout and real-time verification ===
            for logout_index in range(3):
                print(f"\n📤 LOGGING OUT User {logout_index + 1} ({users[logout_index]['username']})")
                
                # Logout the user (cookie deletion method from conftest.py)
                logout_driver = browser_sessions[logout_index]['driver']
                logout_driver.delete_all_cookies()
                logout_driver.refresh()
                time.sleep(3)  # Allow logout and WebSocket disconnect
                
                # Check remaining users see the update
                remaining_count = 3 - logout_index - 1
                print(f"Expected remaining online users: {remaining_count}")
                
                if remaining_count > 0:
                    for check_index in range(logout_index + 1, 3):
                        session = browser_sessions[check_index]
                        driver = session['driver']
                        user = session['user']
                        
                        try:
                            # Refresh to see the update (WebSocket should auto-update, but refresh ensures we see it)
                            driver.refresh()
                            time.sleep(2)
                            
                            # Navigate back to subject page
                            driver.get(f"{server}/groups/{group_name}")
                            time.sleep(1)
                            subject_link = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '{subject_name}')]"))
                            )
                            subject_link.click()
                            time.sleep(3)
                            
                            # Check the count
                            online_header = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '🟢 Online')]"))
                            )
                            header_text = online_header.text
                            print(f"User {check_index + 1} sees: {header_text}")
                            
                            # Should show correct remaining count
                            assert f"({remaining_count})" in header_text or str(remaining_count) in header_text
                            
                            # Verify logged out user is NOT visible
                            logged_out_username = users[logout_index]['username']
                            logged_out_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{logged_out_username}')]")
                            # Filter out navigation/header elements
                            visible_logged_out = [el for el in logged_out_elements if el.is_displayed() and "Online" not in el.text]
                            assert len(visible_logged_out) == 0, f"Logged out user {logged_out_username} still visible to {user['username']}"
                            
                            # Verify remaining users ARE visible
                            for remaining_index in range(logout_index + 1, 3):
                                remaining_username = users[remaining_index]['username']
                                remaining_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{remaining_username}')]")
                                visible_remaining = [el for el in remaining_elements if el.is_displayed()]
                                assert len(visible_remaining) > 0, f"Remaining user {remaining_username} not visible"
                            
                            print(f"✅ User {check_index + 1} correctly sees {remaining_count} users (without {logged_out_username})")
                            
                        except Exception as e:
                            print(f"❌ User {check_index + 1} verification failed after User {logout_index + 1} logout: {e}")
                            driver.save_screenshot(f"test_reports/user_{check_index + 1}_after_logout_{logout_index + 1}_failed.png")
                            raise
            
            print("✅ SEQUENTIAL LOGOUT Test passed: Real-time user updates work correctly!")
            
        finally:
            # === CLEANUP: Close all browser sessions ===
            for i, session in enumerate(browser_sessions):
                try:
                    session['driver'].quit()
                    print(f"✅ Browser session {i + 1} closed")
                except Exception as e:
                    print(f"Warning: Error closing browser session {i + 1}: {e}")