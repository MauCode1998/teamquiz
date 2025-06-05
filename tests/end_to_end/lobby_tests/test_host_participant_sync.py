import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestHostParticipantSync:
    """Test that host sees when participants join the lobby"""
    
    def test_host_sees_participant_join(
        self, 
        driver, 
        server, 
        clean_database,
        api_create_user, 
        api_create_group, 
        api_create_subject,
        api_login,
        login_user_ui,
        navigate_to_group,
        wait_helper
    ):
        """Test that host sees when a participant joins the lobby"""
        
        # Create test users with unique names
        timestamp = int(time.time())
        host_user = f"hostuser{timestamp}"
        participant_user = f"participant{timestamp}"
        print(f"🔥 TEST: Creating test users: {host_user}, {participant_user}")
        api_create_user(host_user, f"{host_user}@test.com", "password123")
        api_create_user(participant_user, f"{participant_user}@test.com", "password123")
        
        # Create group and subject with unique names
        group_name = f"TestGroup{timestamp}"
        subject_name = f"TestSubject{timestamp}"
        print(f"🔥 TEST: Creating group {group_name} and subject {subject_name}...")
        host_auth = api_login(host_user, "password123")
        api_create_group(group_name, host_auth)
        api_create_subject(subject_name, group_name, host_auth)
        
        # Host logs in and creates lobby
        print("🔥 TEST: Host logging in...")
        login_user_ui(host_user, "password123")
        
        print("🔥 TEST: Navigating to group...")
        navigate_to_group(group_name)
        
        # Find and click on subject to create lobby
        print("🔥 TEST: Creating lobby...")
        try:
            subject_link = wait_helper["clickable"](driver, (By.LINK_TEXT, subject_name), 5)
            subject_link.click()
            
            # Wait for subject page to load and click start.jpeg image
            start_image = wait_helper["clickable"](driver, (By.XPATH, "//img[contains(@src, 'start')]"), 5)
            start_image.click()
        except Exception as e:
            print(f"🔥 TEST: Error creating lobby: {e}")
            driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/lobby_creation_failed.png")
            raise
        
        # Wait for lobby page to load
        print("🔥 TEST: Waiting for lobby page...")
        time.sleep(3)  # Give page time to load
        
        # Debug: Take screenshot and check current URL
        print(f"🔥 TEST: Current URL: {driver.current_url}")
        driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/lobby_page_debug.png")
        
        # Try different ways to find the lobby header
        try:
            # First try with CSS selector
            lobby_header = driver.find_element(By.CSS_SELECTOR, "h1.mainPageUeberschrift")
            print(f"🔥 TEST: Found lobby header with CSS: {lobby_header.text}")
        except:
            print("🔥 TEST: Could not find lobby header with CSS selector")
            
        try:
            # Then try with partial text
            lobby_header = driver.find_element(By.XPATH, "//h1[contains(text(), 'Lobby')]")
            print(f"🔥 TEST: Found lobby header with XPath: {lobby_header.text}")
        except Exception as e:
            print(f"🔥 TEST: Could not find lobby header with XPath: {e}")
            # Check if we're in the right frame/window
            print(f"🔥 TEST: Current window handles: {driver.window_handles}")
            print(f"🔥 TEST: Page title: {driver.title}")
            # Try to get page source
            try:
                page_source_snippet = driver.page_source[:500]
                print(f"🔥 TEST: Page source start: {page_source_snippet}")
            except:
                print("🔥 TEST: Could not get page source")
            raise
        
        # Check initial participant count (should be 1 - just the host)
        print("🔥 TEST: Checking initial participant count...")
        participant_header = wait_helper["element"](driver, (By.XPATH, "//h2[contains(text(), 'Beigetreten')]"))
        initial_text = participant_header.text
        print(f"🔥 TEST: Initial participant header: {initial_text}")
        
        # Verify host is shown in participants list
        host_participant = wait_helper["element"](driver, (By.XPATH, f"//li[contains(., '{host_user}') and contains(., 'Host')]"))
        assert host_participant.is_displayed(), "Host should be visible in participants list"
        
        # Get join code for second user
        join_code_element = wait_helper["element"](driver, (By.XPATH, "//strong[parent::*[contains(text(), 'Join Code')]]"))
        join_code = join_code_element.text
        print(f"🔥 TEST: Join code: {join_code}")
        
        # Create WebSocket connection for participant
        print("🔥 TEST: Participant joining via WebSocket...")
        
        # Login participant via API to get token
        participant_auth = api_login(participant_user, "password123")
        
        # First call the join API endpoint
        import requests
        headers = {
            "Authorization": participant_auth["Authorization"]
        }
        join_response = requests.post(
            f"{server}/api/session/join",
            json={"join_code": join_code},
            headers=headers,
            cookies=participant_auth["cookies"]
        )
        
        if join_response.status_code != 200:
            print(f"🔥 TEST: Failed to join: {join_response.status_code} - {join_response.text}")
            raise Exception("Participant could not join session")
            
        session_id = join_response.json()["session_id"]
        print(f"🔥 TEST: Participant got session_id: {session_id}")
        
        # Now create WebSocket connection and send join_lobby
        import websocket
        import json
        
        # Extract token from auth header
        token = participant_auth["Authorization"].replace("Bearer ", "")
        ws_url = f"ws://localhost:8000/ws/{token}"
        
        print(f"🔥 TEST: Connecting participant WebSocket...")
        ws = websocket.WebSocket()
        ws.connect(ws_url)
        
        # Send join_lobby message
        join_msg = json.dumps({
            "type": "join_lobby",
            "session_id": session_id
        })
        ws.send(join_msg)
        print(f"🔥 TEST: Participant sent join_lobby message")
        
        # Give time for WebSocket message to process
        time.sleep(2)
        
        # Wait and check if host sees the participant
        print("🔥 TEST: Waiting for host to see participant...")
        max_wait_time = 15  # 15 seconds max
        participant_found = False
        
        for i in range(max_wait_time):
            try:
                # Check for participant in list
                participant_elements = driver.find_elements(By.XPATH, f"//li[contains(., '{participant_user}')]")
                if participant_elements:
                    participant_found = True
                    print(f"🔥 TEST: ✅ Participant found after {i+1} seconds!")
                    break
                
                # Also check participant count in header
                participant_header = driver.find_element(By.XPATH, "//h2[contains(text(), 'Beigetreten')]")
                current_text = participant_header.text
                print(f"🔥 TEST: Current participant header: {current_text}")
                
                if "(2)" in current_text:
                    participant_found = True
                    print(f"🔥 TEST: ✅ Participant count updated after {i+1} seconds!")
                    break
                    
            except Exception as e:
                print(f"🔥 TEST: Waiting... ({i+1}s) - {e}")
            
            time.sleep(1)
        
        # Take screenshot for debugging
        driver.save_screenshot(f"/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/lobby_participant_sync_{int(time.time())}.png")
        
        # Assert that participant was found
        assert participant_found, f"Host should see participant after {max_wait_time} seconds"
        
        # Final verification - check that both users are in participants list
        print("🔥 TEST: Final verification...")
        participants = driver.find_elements(By.XPATH, "//li[contains(@class, 'MuiListItem-root')]")
        participant_names = [p.text for p in participants if p.text.strip()]
        print(f"🔥 TEST: Final participants list: {participant_names}")
        
        # Should have both host and participant
        assert len([p for p in participant_names if host_user in p]) > 0, "Host should be in participants list"
        assert len([p for p in participant_names if participant_user in p]) > 0, "Participant should be in participants list"
        
        # Clean up WebSocket
        ws.close()
        
        print("🔥 TEST: ✅ Test completed successfully!")