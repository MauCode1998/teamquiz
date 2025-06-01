"""
Test sequential logout using API + UI combination
2 users login via API (WebSocket), 1 user via UI watches real-time updates
"""
import pytest
import time
import requests
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.test_data import generate_test_user, generate_test_group, generate_test_subject


class TestAPILogoutRealtime:
    """Test real-time updates when API users logout while UI user watches"""

    def test_two_api_users_logout_ui_user_watches(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login,
        login_user_ui, logout_user_ui, navigate_to_group
    ):
        """2 users login via API, 1 UI user watches them logout sequentially"""
        print("\n🎬 Starting API LOGOUT test: 2 API users logout, UI user watches")
        
        # === SETUP: Create test data ===
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        
        # Create 3 users: 2 for API, 1 for UI
        ui_user = generate_test_user()
        api_user1 = generate_test_user()
        api_user2 = generate_test_user()
        users = [ui_user, api_user1, api_user2]
        
        for user in users:
            api_create_user(user["username"], user["email"], user["password"])
        
        # Create group and subject
        auth_data = api_login(ui_user["username"], ui_user["password"])
        api_create_group(group_name, auth_data)
        api_create_subject(subject_name, group_name, auth_data)
        
        print(f"✅ SETUP: Created 3 users and group '{group_name}'")
        print(f"  UI User: {ui_user['username']}")
        print(f"  API User 1: {api_user1['username']}")
        print(f"  API User 2: {api_user2['username']}")
        
        # === STEP 1: Login UI user and navigate to subject ===
        login_user_ui(ui_user["username"], ui_user["password"])
        navigate_to_group(group_name)
        time.sleep(1)
        
        # Navigate to subject page (where OnlineUsers component is)
        subject_link = driver.find_element(By.XPATH, f"//a[contains(@href, '{subject_name}')]")
        subject_link.click()
        time.sleep(2)  # Allow WebSocket to connect
        
        # Verify UI user sees themselves online (count = 1)
        online_header = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '🟢 Online')]"))
        )
        assert "(1)" in online_header.text
        print(f"✅ UI user sees: {online_header.text}")
        
        # === STEP 2: Create WebSocket connections for API users ===
        api_websockets = []
        
        for i, api_user in enumerate([api_user1, api_user2]):
            # Login via API to get token
            api_auth = api_login(api_user["username"], api_user["password"])
            token = api_auth["Authorization"].replace("Bearer ", "")
            
            # Create WebSocket connection (simulating what OnlineUsers.js does)
            import websocket
            import json
            
            ws_url = f"ws://localhost:8000/ws/{token}"
            ws = websocket.create_connection(ws_url)
            
            # Send join_group message
            join_message = {
                "type": "join_group",
                "group_name": group_name
            }
            ws.send(json.dumps(join_message))
            
            api_websockets.append({
                'websocket': ws,
                'user': api_user,
                'index': i + 1
            })
            
            print(f"✅ API User {i + 1} ({api_user['username']}) connected via WebSocket")
            time.sleep(1)  # Allow WebSocket to register and update UI
            
            # Check updated count
            online_header = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '🟢 Online')]"))
            )
            expected_count = i + 2  # UI user + (i+1) API users
            header_text = online_header.text
            print(f"After API User {i + 1} joins: {header_text}")
            assert f"({expected_count})" in header_text or str(expected_count) in header_text
            
            # Verify API user's name is visible
            username_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{api_user['username']}')]")
            visible_elements = [el for el in username_elements if el.is_displayed()]
            assert len(visible_elements) > 0, f"API user {api_user['username']} not visible"
            
            print(f"✅ UI user sees API User {i + 1} ({api_user['username']}) online")
        
        print("✅ All 3 users online, UI user sees count (3)")
        
        # === STEP 3: Sequential logout of API users ===
        # UI user stays on subject page - real-time WebSocket updates should show changes without navigation
        for logout_index, api_ws in enumerate(api_websockets):
            api_user = api_ws['user']
            ws = api_ws['websocket']
            
            print(f"\n📤 DISCONNECTING API User {logout_index + 1} ({api_user['username']})")
            
            # Close WebSocket connection (simulates logout)
            ws.close()
            time.sleep(2)  # Allow WebSocket disconnect to propagate (real-time update)
            
            # Check updated count
            remaining_count = 3 - logout_index - 1  # Total - logged_out_count
            print(f"Expected remaining count: {remaining_count}")
            
            try:
                online_header = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '🟢 Online')]"))
                )
                header_text = online_header.text
                print(f"After API User {logout_index + 1} logout: {header_text}")
                
                # Should show correct remaining count
                assert f"({remaining_count})" in header_text or str(remaining_count) in header_text
                
                # Verify logged out API user is NOT visible
                logged_out_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{api_user['username']}')]")
                visible_logged_out = [el for el in logged_out_elements if el.is_displayed() and "Online" not in el.text]
                assert len(visible_logged_out) == 0, f"Logged out API user {api_user['username']} still visible"
                
                # Verify remaining users ARE visible
                if remaining_count > 1:  # If there are still API users online
                    for remaining_index in range(logout_index + 1, len(api_websockets)):
                        remaining_user = api_websockets[remaining_index]['user']
                        remaining_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{remaining_user['username']}')]")
                        visible_remaining = [el for el in remaining_elements if el.is_displayed()]
                        assert len(visible_remaining) > 0, f"Remaining API user {remaining_user['username']} not visible"
                
                # UI user should always be visible
                ui_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{ui_user['username']}')]")
                visible_ui = [el for el in ui_elements if el.is_displayed()]
                assert len(visible_ui) > 0, f"UI user {ui_user['username']} not visible"
                
                print(f"✅ UI user correctly sees {remaining_count} users (API User {logout_index + 1} disappeared)")
                
            except Exception as e:
                print(f"❌ Verification failed after API User {logout_index + 1} logout: {e}")
                driver.save_screenshot(f"test_reports/api_logout_{logout_index + 1}_failed.png")
                raise
        
        # === CLEANUP: Close any remaining WebSocket connections ===
        for api_ws in api_websockets:
            try:
                if api_ws['websocket'].connected:
                    api_ws['websocket'].close()
            except:
                pass
        
        print("✅ API LOGOUT Test passed: Real-time updates work with API user disconnections!")