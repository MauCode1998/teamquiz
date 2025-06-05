import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestLobbyMultiUser:
    """Test multi-user lobby functionality - the actual problem we need to solve"""
    
    def test_host_sees_participant_join_realtime(
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
        """The REAL test - Host should see when participant joins lobby in real-time"""
        
        print("🔥 TEST: Starting multi-user lobby test...")
        
        # Create unique usernames
        import time
        timestamp = int(time.time())
        host_user = f"host{timestamp}"
        participant_user = f"participant{timestamp}"
        group_name = f"TestGroup{timestamp}"
        subject_name = f"TestSubject{timestamp}"
        
        print(f"🔥 TEST: Creating users: {host_user}, {participant_user}")
        print(f"🔥 TEST: Creating group: {group_name}, subject: {subject_name}")
        
        # Create users
        api_create_user(host_user, f"{host_user}@test.com", "password123")
        api_create_user(participant_user, f"{participant_user}@test.com", "password123")
        
        # Get auth for host
        host_auth = api_login(host_user, "password123")
        
        # Create group and subject
        api_create_group(group_name, host_auth)
        api_create_subject(subject_name, group_name, host_auth)
        
        print("🔥 TEST: ✅ Setup completed")
        
        # HOST FLOW: Login and create lobby
        print("🔥 TEST: HOST - Logging in...")
        login_user_ui(host_user, "password123")
        
        print("🔥 TEST: HOST - Navigating to group...")
        navigate_to_group(group_name)
        
      
        
        # Click on subject
        try:
            subject_link = wait_helper["clickable"](driver, (By.LINK_TEXT, subject_name), 5)
            subject_link.click()
        except:
            print(f"🔥 TEST: Could not find subject {subject_name}")
            driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/debug_no_subject.png")
            raise
        
        # Debug screenshot
        driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/debug_subject_page.png")
        
        # Create lobby by clicking the start.jpeg image
        try:
            start_image = wait_helper["clickable"](driver, (By.XPATH, "//img[contains(@src, 'start')]"), 5)
            start_image.click()
        except Exception as e:
            print(f"🔥 TEST: Error clicking start image: {e}")
            driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/debug_start_button_error.png")
            raise
        
        # Wait for lobby to load
        wait_helper["element"](driver, (By.XPATH, "//h1[contains(text(), 'Lobby')]"))
        
        # Get join code
        join_code_element = wait_helper["element"](driver, (By.XPATH, "//strong[parent::*[contains(text(), 'Join Code')]]"))
        join_code = join_code_element.text
        print(f"🔥 TEST: Join code: {join_code}")
        
        # Verify initial state - only host
        print("🔥 TEST: Checking initial participant count...")
        participant_header = driver.find_element(By.XPATH, "//h2[contains(text(), 'Beigetreten')]")
        initial_text = participant_header.text
        print(f"🔥 TEST: Initial header: '{initial_text}'")
        
        # Should show (1) for host only
        assert "(1)" in initial_text, f"Should show (1) participant initially, got: {initial_text}"
        
        # Take screenshot before participant joins
        driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/before_participant_join.png")
        
        # PARTICIPANT FLOW: Open second window
        print("🔥 TEST: PARTICIPANT - Opening second browser window...")
        original_window = driver.current_window_handle
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        
        # Login as participant
        driver.get(server)
        login_user_ui(participant_user, "password123")
        
        # Join lobby with code
        print(f"🔥 TEST: PARTICIPANT - Joining lobby with code {join_code}...")
        driver.get(f"{server}/lobby?group={group_name}&subject={subject_name}&code={join_code}")
        
        # Wait for participant lobby to load
        wait_helper["element"](driver, (By.XPATH, "//h1[contains(text(), 'Lobby')]"))
        
        # Switch back to host window - THE CRITICAL TEST
        print("🔥 TEST: HOST - Switching back to check if participant is visible...")
        driver.switch_to.window(original_window)
        
        # Wait for host to see participant - THIS IS THE BUG WE'RE FIXING
        print("🔥 TEST: HOST - Waiting for participant to appear...")
        participant_found = False
        
        for i in range(20):  # 20 seconds max wait
            try:
                # Check participant count in header
                participant_header = driver.find_element(By.XPATH, "//h2[contains(text(), 'Beigetreten')]")
                current_text = participant_header.text
                print(f"🔥 TEST: HOST - Second {i+1}: Header shows '{current_text}'")
                
                # Check for participant in list
                participant_items = driver.find_elements(By.XPATH, f"//li[contains(., '{participant_user}')]")
                
                if "(2)" in current_text or len(participant_items) > 0:
                    participant_found = True
                    print(f"🔥 TEST: ✅ HOST - Participant found after {i+1} seconds!")
                    break
                    
            except Exception as e:
                print(f"🔥 TEST: HOST - Error checking participants: {e}")
            
            time.sleep(1)
        
        # Take screenshot after participant should have joined
        driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/after_participant_join.png")
        
        # THE ASSERTION THAT TESTS OUR FIX
        if not participant_found:
            print("🔥 TEST: ❌ FAILED - Host never saw participant join!")
            print("🔥 TEST: This is the bug we need to fix!")
            
            # Switch to participant window to verify they actually joined
            driver.switch_to.window(driver.window_handles[1])
            participant_header = driver.find_element(By.XPATH, "//h2[contains(text(), 'Beigetreten')]")
            participant_view = participant_header.text
            print(f"🔥 TEST: PARTICIPANT - sees: '{participant_view}'")
            
            # Take debug screenshot from participant view
            driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/participant_view.png")
            
        assert participant_found, "🔥 BUG: Host should see participant join within 20 seconds!"
        
        print("🔥 TEST: ✅ SUCCESS - Host sees participant join in real-time!")
        print("🔥 TEST: Multi-user lobby sync working correctly!")
        
        # Final verification - both users should see both participants
        final_header = driver.find_element(By.XPATH, "//h2[contains(text(), 'Beigetreten')]")
        final_text = final_header.text
        print(f"🔥 TEST: Final state: {final_text}")
        
        assert "(2)" in final_text, f"Should show (2) participants at end, got: {final_text}"