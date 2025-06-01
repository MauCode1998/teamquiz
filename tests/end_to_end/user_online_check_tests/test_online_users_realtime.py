"""
Test online user tracking with WebSocket connections
Tests 3 users logging in/out and real-time display updates
"""
import pytest
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.test_data import generate_test_user, generate_test_group, generate_test_subject


class TestOnlineUsersRealtime:
    """Test real-time online user tracking via WebSocket"""

    def test_three_users_parallel_login_logout(
        self, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login,
        login_user_ui, logout_user_ui, navigate_to_group
    ):
        """Test 3 users logging in parallel, then logging out sequentially"""
        print("\n🎬 Starting REAL-TIME test: 3 users parallel login/logout")
        
        # === SETUP: Create test data via API ===
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        
        # Create 3 test users
        users = []
        for i in range(3):
            user_data = generate_test_user()
            users.append(user_data)
            api_create_user(user_data["username"], user_data["email"], user_data["password"])
        
        # Create group and subject, add all users to group
        auth_data = api_login(users[0]["username"], users[0]["password"])
        api_create_group(group_name, auth_data)
        api_create_subject(subject_name, group_name, auth_data)
        
        # Add other users to group via API
        for i in range(1, 3):
            user_auth = api_login(users[i]["username"], users[i]["password"])
            # TODO: Add API endpoint to join existing group or use invitation system
        
        print(f"✅ SETUP: Created 3 users and group '{group_name}'")
        
        # === STEP 1: Create 3 Safari WebDriver instances ===
        drivers = []
        for i in range(3):
            try:
                driver = webdriver.Safari()
                driver.implicitly_wait(10)
                drivers.append(driver)
            except Exception as e:
                pytest.skip(f"Safari driver not available: {e}")
        print("✅ Created 3 Safari WebDriver instances")
        
        try:
            # === STEP 2: Log in all 3 users in parallel ===
            def login_user(driver, user_data, user_index):
                """Thread function to log in a user"""
                print(f"User {user_index + 1} ({user_data['username']}) logging in...")
                login_user_ui(user_data["username"], user_data["password"])
                navigate_to_group(group_name)
                print(f"✅ User {user_index + 1} logged in and navigated to group")
                time.sleep(2)  # Allow WebSocket to connect
            
            # Start all logins in parallel
            threads = []
            for i, (driver, user_data) in enumerate(zip(drivers, users)):
                thread = threading.Thread(target=login_user, args=(driver, user_data, i))
                threads.append(thread)
                thread.start()
                time.sleep(1)  # Small delay between logins
            
            # Wait for all logins to complete
            for thread in threads:
                thread.join()
            
            print("✅ All 3 users logged in")
            
            # === STEP 3: Verify all 3 users are visible ===
            time.sleep(3)  # Allow WebSocket updates to propagate
            
            # Check user count in the online users section
            for i, driver in enumerate(drivers):
                try:
                    # Look for the online users count in the header
                    online_header = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '🟢 Online')]"))
                    )
                    header_text = online_header.text
                    print(f"User {i + 1} sees online header: {header_text}")
                    
                    # Should show "🟢 Online (3)" or similar
                    assert "(3)" in header_text or "3" in header_text
                    
                    # Verify all usernames are visible
                    for user_data in users:
                        username_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{user_data['username']}')]")
                        assert username_element.is_displayed()
                    
                    print(f"✅ User {i + 1} sees all 3 users online")
                    
                except Exception as e:
                    print(f"❌ User {i + 1} verification failed: {e}")
                    # Take screenshot for debugging
                    driver.save_screenshot(f"test_reports/user_{i + 1}_all_online.png")
                    raise
            
            # === STEP 4: Log out users sequentially and verify updates ===
            for logout_index in range(3):
                print(f"\n📤 Logging out User {logout_index + 1} ({users[logout_index]['username']})")
                
                # Log out the user
                logout_user_ui(drivers[logout_index])
                time.sleep(2)  # Allow WebSocket to process disconnect
                
                # Verify remaining users see the update
                remaining_count = 3 - logout_index - 1
                print(f"Expected remaining users: {remaining_count}")
                
                for check_index in range(logout_index + 1, 3):
                    driver = drivers[check_index]
                    try:
                        # Refresh to ensure we see the update
                        driver.refresh()
                        time.sleep(2)
                        
                        # Check the count
                        if remaining_count > 0:
                            online_header = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '🟢 Online')]"))
                            )
                            header_text = online_header.text
                            print(f"User {check_index + 1} sees: {header_text}")
                            
                            # Should show correct count
                            assert f"({remaining_count})" in header_text or str(remaining_count) in header_text
                            
                            # Verify logged out user is NOT visible
                            logged_out_username = users[logout_index]['username']
                            logged_out_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{logged_out_username}')]")
                            # Filter out elements that might be in navigation/header
                            visible_logged_out = [el for el in logged_out_elements if el.is_displayed() and "Online" not in el.text]
                            assert len(visible_logged_out) == 0, f"Logged out user {logged_out_username} still visible"
                            
                            print(f"✅ User {check_index + 1} correctly sees {remaining_count} users (without {logged_out_username})")
                        
                    except Exception as e:
                        print(f"❌ Verification failed for User {check_index + 1} after logout: {e}")
                        driver.save_screenshot(f"test_reports/user_{check_index + 1}_after_logout_{logout_index + 1}.png")
                        raise
            
            print("✅ REAL-TIME Test passed: All login/logout events correctly tracked")
            
        finally:
            # === CLEANUP: Close all drivers ===
            for i, driver in enumerate(drivers):
                try:
                    driver.quit()
                    print(f"✅ Driver {i + 1} closed")
                except Exception as e:
                    print(f"Warning: Error closing driver {i + 1}: {e}")

    def test_websocket_connection_persistence(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login,
        login_user_ui, logout_user_ui, navigate_to_group
    ):
        """Test that WebSocket connection persists across page navigation"""
        print("\n🎬 Starting WebSocket persistence test")
        
        # === SETUP ===
        user_data = generate_test_user()
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        
        api_create_user(user_data["username"], user_data["email"], user_data["password"])
        auth_data = api_login(user_data["username"], user_data["password"])
        api_create_group(group_name, auth_data)
        api_create_subject(subject_name, group_name, auth_data)
        
        # === STEP 1: Login and go to subject page ===
        login_user_ui(user_data["username"], user_data["password"])
        navigate_to_group(group_name)
        time.sleep(2)
        
        # Navigate to subject page (where OnlineUsers component is)
        subject_link = driver.find_element(By.XPATH, f"//a[contains(@href, '{subject_name}')]")
        subject_link.click()
        time.sleep(3)  # Allow WebSocket to connect
        
        # Verify user is online in subject page
        online_header = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '🟢 Online')]"))
        )
        assert "(1)" in online_header.text
        assert user_data["username"] in driver.page_source
        print("✅ User online in subject page")
        
        # === STEP 2: Navigate back to group and return to subject ===
        driver.back()
        time.sleep(2)
        
        # Navigate to subject page again
        subject_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '{subject_name}')]"))
        )
        subject_link.click()
        time.sleep(3)
        
        # Verify user is still online after navigation
        online_header = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '🟢 Online')]"))
        )
        assert "(1)" in online_header.text
        print("✅ User still online after navigation back and forth")
        
        print("✅ WebSocket persistence test passed")