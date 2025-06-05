import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestLobbyBasic:
    """Basic lobby functionality tests"""
    
    def test_can_create_lobby(
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
        """Test that a user can create a lobby"""
        
        print("🔥 TEST: Starting basic lobby test...")
        
        # Create test user with unique name
        import time
        timestamp = int(time.time())
        username = f"testuser{timestamp}"
        group_name = f"TestGroup{timestamp}"
        subject_name = f"TestSubject{timestamp}"
        
        print(f"🔥 TEST: Creating test user {username}...")
        api_create_user(username, f"{username}@test.com", "password123")
        
        # Login via API to get auth data  
        print("🔥 TEST: Getting auth data...")
        # Use the api_login fixture which returns proper auth format
        auth_data = api_login(username, "password123")
        
        # Create group and subject
        print(f"🔥 TEST: Creating group {group_name} and subject {subject_name}...")
        try:
            api_create_group(group_name, auth_data)
            print("🔥 TEST: Group created")
        except Exception as e:
            print(f"🔥 TEST: Group creation error: {e}")
            raise
        
        try:
            api_create_subject(subject_name, group_name, auth_data)
            print("🔥 TEST: Subject created")
        except Exception as e:
            print(f"🔥 TEST: Subject creation error: {e}")
            raise
        
        # Login
        print("🔥 TEST: Logging in...")
        login_user_ui(username, "password123")
        time.sleep(2)
        
        # Navigate to groups page
        print("🔥 TEST: Navigating to groups...")
        driver.get(f"{server}/groups")
        time.sleep(2)
        
        # Take screenshot
        driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/groups_page.png")
        
        # Try to find TestGroup
        try:
            group_link = driver.find_element(By.LINK_TEXT, group_name)
            print(f"🔥 TEST: Found {group_name} link")
            group_link.click()
            time.sleep(2)
        except Exception as e:
            print(f"🔥 TEST: Could not find {group_name}: {e}")
            driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/no_testgroup.png")
            raise
        
        # Take screenshot of group page
        driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/group_page.png")
        
        # Try to find TestSubject
        try:
            subject_link = driver.find_element(By.LINK_TEXT, subject_name)
            print(f"🔥 TEST: Found {subject_name} link")
            subject_link.click()
            time.sleep(2)
        except Exception as e:
            print(f"🔥 TEST: Could not find {subject_name}: {e}")
            driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/no_testsubject.png")
            raise
        
        # Take screenshot of subject page
        driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/subject_page.png")
        
        # Try to find "Spiel starten" image (that leads to lobby)
        try:
            # The lobby creation is triggered by clicking on start.jpeg image
            start_img = driver.find_element(By.XPATH, "//img[contains(@src, 'start')]")
            print("🔥 TEST: Found start image")
            start_img.click()
            time.sleep(3)
        except Exception as e:
            print(f"🔥 TEST: Could not find start image: {e}")
            driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/no_start_button.png")
            raise
        
        # Check if we're in lobby
        try:
            lobby_title = driver.find_element(By.XPATH, "//h1[contains(text(), 'Lobby')]")
            print("🔥 TEST: ✅ Successfully created lobby!")
            driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/lobby_created.png")
        except Exception as e:
            print(f"🔥 TEST: Not in lobby yet: {e}")
            driver.save_screenshot("/Users/mau/Desktop/Coding.nosync/TeamQuiz/test_reports/lobby_failed.png")
            raise
        
        print("🔥 TEST: ✅ Basic lobby test completed successfully!")