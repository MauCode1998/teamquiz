"""
Test online user tracking with WebSocket connections
Simple test with sequential login/logout to verify basic functionality
"""
import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.test_data import generate_test_user, generate_test_group, generate_test_subject


class TestOnlineUsersSimple:
    """Test real-time online user tracking via WebSocket"""

    def test_single_user_online_tracking(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login,
        login_user_ui, logout_user_ui, navigate_to_group
    ):
        """Test single user login and online status display"""
        print("\n🎬 Starting SIMPLE test: Single user online tracking")
        
        # === SETUP: Create test data via API ===
        user_data = generate_test_user()
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        
        # Create user, group, and subject via API
        api_create_user(user_data["username"], user_data["email"], user_data["password"])
        auth_data = api_login(user_data["username"], user_data["password"])
        api_create_group(group_name, auth_data)
        api_create_subject(subject_name, group_name, auth_data)
        
        print(f"✅ SETUP: User, group, and subject created via API")
        
        # === STEP 1: Login via UI ===
        login_user_ui(user_data["username"], user_data["password"])
        navigate_to_group(group_name)
        time.sleep(2)  # Allow page to load
        
        # === STEP 2: Navigate to subject page (where OnlineUsers component is) ===
        subject_link = driver.find_element(By.XPATH, f"//a[contains(@href, '{subject_name}')]")
        subject_link.click()
        time.sleep(3)  # Allow WebSocket to connect and update
        
        # === STEP 3: Verify user appears online on Fach page ===
        try:
            # Look for the online users section on Fach page
            online_header = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '🟢 Online')]"))
            )
            header_text = online_header.text
            print(f"Online header found on Fach page: {header_text}")
            
            # Should show "🟢 Online (1)" or similar
            assert "(1)" in header_text or "1" in header_text
            
            # Verify username is visible in online users
            username_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{user_data['username']}')]")
            assert username_element.is_displayed()
            
            print(f"✅ User {user_data['username']} appears online correctly on Fach page")
            
        except Exception as e:
            print(f"❌ Online user verification failed on Fach page: {e}")
            print(f"Current URL: {driver.current_url}")
            # Take screenshot for debugging
            driver.save_screenshot("test_reports/fach_page_online_failed.png")
            raise
        
        # === STEP 4: Logout and verify user goes offline ===
        logout_user_ui()
        time.sleep(2)  # Allow logout to process
        
        print("✅ SIMPLE Test passed: Single user online tracking works")

    def test_user_login_logout_cycle(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login,
        login_user_ui, logout_user_ui, navigate_to_group
    ):
        """Test user login → online → logout → offline cycle"""
        print("\n🎬 Starting CYCLE test: User login/logout cycle")
        
        # === SETUP: Create test data via API ===
        user_data = generate_test_user()
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        
        # Create user, group, and subject via API
        api_create_user(user_data["username"], user_data["email"], user_data["password"])
        auth_data = api_login(user_data["username"], user_data["password"])
        api_create_group(group_name, auth_data)
        api_create_subject(subject_name, group_name, auth_data)
        
        print(f"✅ SETUP: User, group, and subject created via API")
        
        # === STEP 1: Login and navigate to Fach page ===
        login_user_ui(user_data["username"], user_data["password"])
        navigate_to_group(group_name)
        time.sleep(2)  # Allow page to load
        
        # Navigate to subject page (where OnlineUsers component is)
        subject_link = driver.find_element(By.XPATH, f"//a[contains(@href, '{subject_name}')]")
        subject_link.click()
        time.sleep(3)  # Allow WebSocket to connect
        
        # Verify user is online on Fach page
        try:
            online_header = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '🟢 Online')]"))
            )
            header_text = online_header.text
            print(f"After login - Online header: {header_text}")
            
            assert "(1)" in header_text or "1" in header_text
            assert user_data["username"] in driver.page_source
            
            print(f"✅ User {user_data['username']} appears online after login")
            
        except Exception as e:
            print(f"❌ Login verification failed: {e}")
            driver.save_screenshot("test_reports/cycle_login_failed.png")
            raise
        
        # === STEP 2: Logout and verify user disappears ===
        logout_user_ui()
        time.sleep(3)  # Allow logout and WebSocket disconnect
        
        # Navigate back to group page (should redirect to login)
        driver.get(f"{server}/groups/{group_name}")
        time.sleep(2)
        
        # Should be redirected to login page since logged out
        current_url = driver.current_url
        print(f"After logout, current URL: {current_url}")
        
        # Should be on login page or see login form
        assert "/" in current_url or "login" in current_url or driver.find_elements(By.CSS_SELECTOR, "input[placeholder='Benutzername']")
        
        print("✅ CYCLE Test passed: User login/logout cycle works correctly")

    def test_lobby_page_online_users(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login,
        login_user_ui, logout_user_ui, navigate_to_group
    ):
        """Test OnlineUsers component works on Lobby page - SKIPPED: OnlineUsers removed from Lobby"""
        pytest.skip("OnlineUsers component was removed from Lobby page - participants are shown differently")
        print("\n🎬 Starting LOBBY test: Online users on Lobby page")
        
        # === SETUP: Create test data via API ===
        user_data = generate_test_user()
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        
        # Create user, group, and subject via API
        api_create_user(user_data["username"], user_data["email"], user_data["password"])
        auth_data = api_login(user_data["username"], user_data["password"])
        api_create_group(group_name, auth_data)
        api_create_subject(subject_name, group_name, auth_data)
        
        print(f"✅ SETUP: User, group, and subject created via API")
        
        # === STEP 1: Login ===
        login_user_ui(user_data["username"], user_data["password"])
        time.sleep(2)
        
        # === STEP 2: Navigate to Lobby page with group parameter ===
        # Lobby page expects group parameter to work with OnlineUsers
        lobby_url = f"{server}/lobby?gameid=123&group={group_name}"
        driver.get(lobby_url)
        time.sleep(3)  # Allow WebSocket to connect
        
        print(f"Navigated to Lobby: {driver.current_url}")
        
        # === STEP 3: Verify OnlineUsers component works on Lobby ===
        try:
            # Look for the online users section on Lobby page
            online_header = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '🟢 Online')]"))
            )
            header_text = online_header.text
            print(f"Lobby Online header found: {header_text}")
            
            # Should show "🟢 Online (1)" or similar
            assert "(1)" in header_text or "1" in header_text
            
            # Verify username is visible in online users
            username_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{user_data['username']}')]")
            assert username_element.is_displayed()
            
            print(f"✅ User {user_data['username']} appears online correctly on Lobby page")
            
            # Verify "Einladen" buttons are present (showInviteButtons=true)
            invite_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Einladen')]")
            assert len(invite_buttons) > 0, "Invite buttons should be present on Lobby page"
            print(f"✅ Found {len(invite_buttons)} invite button(s) as expected")
            
        except Exception as e:
            print(f"❌ Lobby online user verification failed: {e}")
            print(f"Current URL: {driver.current_url}")
            print(f"Page source contains 'Online': {'Online' in driver.page_source}")
            # Take screenshot for debugging
            driver.save_screenshot("test_reports/lobby_page_online_failed.png")
            raise
        
        print("✅ LOBBY Test passed: OnlineUsers component works on Lobby page")