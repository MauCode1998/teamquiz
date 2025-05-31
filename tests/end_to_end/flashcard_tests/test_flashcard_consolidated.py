import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import time


class TestFlashcardConsolidated:
    """Consolidated flashcard tests including multi-user scenarios"""
    
    def _register_user(self, driver, server, user_data):
        """Register a user using pattern from test_simple_invitation.py"""
        driver.get(f"{server}/register")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "form")))
        
        driver.find_element(By.NAME, "username").send_keys(user_data["username"])
        driver.find_element(By.NAME, "email").send_keys(user_data["email"])
        driver.find_element(By.NAME, "password").send_keys(user_data["password"])
        driver.find_element(By.NAME, "confirmPassword").send_keys(user_data["password"])
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(driver, 10).until(EC.url_contains("/groups"))
        print(f"✅ User {user_data['username']} registered")
    
    def _logout(self, driver, server):
        """Logout current user using pattern from test_simple_invitation.py"""
        print("🔄 Logging out")
        driver.delete_all_cookies()
        driver.get(f"{server}")
        print("✅ Logged out")
    
    def _login(self, driver, server, user_data):
        """Login existing user"""
        print(f"🔄 Logging in {user_data['username']}")
        driver.get(f"{server}")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)
        
        if "/groups" in driver.current_url:
            print(f"✅ Already logged in")
            return
            
        # Find login form fields
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Benutzername']"))
        )
        password_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Passwort']")
        
        username_field.send_keys(user_data["username"])
        password_field.send_keys(user_data["password"])
        
        # Find and click login button
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Anmelden')]")
        login_button.click()
        
        WebDriverWait(driver, 10).until(EC.url_contains("/groups"))
        print(f"✅ Logged in as {user_data['username']}")
    
    def _create_group(self, driver, server, group_name):
        """Create a group using pattern from test_simple_invitation.py"""
        driver.get(f"{server}/groups")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        group_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Gruppenname']")
        group_input.clear()
        group_input.send_keys(group_name)
        
        submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Erstellen!')]")
        submit_button.click()
        
        # Wait briefly for group creation
        time.sleep(0.5)
        print(f"✅ Group '{group_name}' created")
    
    def _navigate_to_group(self, driver, group_name):
        """Navigate to a specific group"""
        group_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, group_name))
        )
        group_link.click()
        WebDriverWait(driver, 10).until(EC.url_contains(f"/groups/{group_name}"))
    
    def _create_subject(self, driver, subject_name):
        """Create a subject in current group using working pattern"""
        # Check if input field is already visible (accordion open)
        try:
            subject_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Neuer Fach Name']")
            if subject_input.is_displayed():
                print("   Accordion already open, using existing input field")
            else:
                raise Exception("Input not visible")
        except:
            # Accordion is closed, need to click it
            print("   Opening accordion...")
            fach_accordion = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Fach hinzufügen')]"))
            )
            fach_accordion.click()
            time.sleep(0.5)
            
            # Now wait for input field
            subject_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='Neuer Fach Name']"))
            )
        
        # Enter subject name
        subject_input.clear()
        subject_input.send_keys(subject_name)
        
        # Save
        save_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Speichern')]")
        save_button.click()
        time.sleep(2)
        print(f"✅ Subject '{subject_name}' created")
    
    def _navigate_to_subject(self, driver, subject_name):
        """Navigate to a specific subject"""
        subject_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, subject_name))
        )
        subject_link.click()
        time.sleep(2)
    
    def _send_invitation(self, driver, invitee_username):
        """Send invitation through frontend UI - pattern from test_simple_invitation.py"""
        print(f"🔄 Sending invitation to {invitee_username}")
        
        # Wait for invitation form to be present (no accordion needed)
        invite_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Benutzername']"))
        )
        
        invite_input.clear()
        invite_input.send_keys(invitee_username)
        
        invite_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Einladen')]")
        invite_button.click()
        
        time.sleep(1)  # Brief wait for invitation to be processed
        print(f"✅ Invitation sent to {invitee_username}")
    
    def _wait_for_invitation(self, driver, server, group_name, timeout=30):
        """Wait for invitation to appear - pattern from test_simple_invitation.py"""
        print(f"🔄 Waiting up to {timeout}s for invitation to appear...")
        
        driver.get(f"{server}/groups")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        end_time = time.time() + timeout
        attempt = 0
        
        while time.time() < end_time:
            attempt += 1
            
            # Refresh the page to trigger invitation loading
            if attempt > 1:
                driver.refresh()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            time.sleep(1)  # Brief wait for async loading
            
            page_text = driver.find_element(By.TAG_NAME, "body").text
            print(f"⏳ Attempt {attempt}: Checking for invitations...")
            
            # Check for invitation indicators
            if "lädt" in page_text and (group_name in page_text or "TestGroup" in page_text):
                print(f"✅ Invitation found on attempt {attempt}!")
                return True
            elif "lädt" in page_text:
                print(f"⚠️ Found invitation text but not for our group")
            else:
                print(f"⏳ No invitation text found yet")
        
        print(f"❌ No invitation found after {timeout}s")
        return False
    
    def _accept_invitation(self, driver):
        """Accept any visible invitation - pattern from test_simple_invitation.py"""
        print("🔄 Looking for accept button...")
        
        try:
            # Look for any "Annehmen" button
            accept_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Annehmen')]"))
            )
            
            print("✅ Found accept button, clicking...")
            accept_button.click()
            
            time.sleep(1)  # Brief wait for acceptance to process
            print("✅ Invitation accepted!")
            
        except Exception as e:
            print(f"❌ Could not find/click accept button: {e}")
            raise
    
    def _create_flashcard_helper(self, driver, question_data):
        """Helper to fill and save a single flashcard"""
        # Fill question
        question_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='Geben Sie hier die Frage ein']"))
        )
        question_input.clear()
        question_input.send_keys(question_data["question"])
        
        # Fill answers
        answer_inputs = driver.find_elements(By.XPATH, "//input[starts-with(@placeholder, 'Antwort')]")
        for i, answer in enumerate(question_data["answers"]):
            answer_inputs[i].clear()
            answer_inputs[i].send_keys(answer)
        
        # Select correct answer
        radio_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        radio_buttons[question_data["correct_index"]].click()
        
        # Save
        save_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Karteikarte speichern')]")
        save_button.click()
        time.sleep(1)
    
    def _create_flashcards(self, driver):
        """Create 3 flashcards"""
        print("🔄 Creating flashcards...")
        
        # Open flashcard accordion
        flashcard_accordion = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Frage hinzufügen')]"))
        )
        flashcard_accordion.click()
        time.sleep(1)
        
        # Flashcard data
        flashcards = [
            {
                "question": "Was ist die Hauptstadt von Deutschland?",
                "answers": ["Berlin", "München", "Hamburg", "Frankfurt"],
                "correct_index": 0
            },
            {
                "question": "Welche Farbe hat der Himmel?",
                "answers": ["Rot", "Grün", "Blau", "Gelb"],
                "correct_index": 2
            },
            {
                "question": "Wie viele Tage hat eine Woche?",
                "answers": ["5", "6", "7", "8"],
                "correct_index": 2
            }
        ]
        
        # Create each flashcard
        for i, card_data in enumerate(flashcards):
            print(f"   Creating flashcard {i+1}/3...")
            self._create_flashcard_helper(driver, card_data)
            print(f"   ✅ Flashcard {i+1} created")
        
        print("✅ All 3 flashcards created successfully")
    
    def test_multiuser_flashcard_scenario(self, driver, server, clean_database):
        """Test complete multi-user flashcard scenario"""
        print("\n🎬 Starting test: Multi-user flashcard scenario")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Test data
        user1_data = {
            "username": f"user1{timestamp}",
            "email": f"user1_{timestamp}@test.com", 
            "password": "password123"
        }
        user2_data = {
            "username": f"user2{timestamp}",
            "email": f"user2_{timestamp}@test.com",
            "password": "password123"
        }
        group_name = f"TestGroup{timestamp}"
        subject_name = f"TestSubject{timestamp}"
        
        try:
            # Step 1: Register both users
            print("\n📍 Step 1: Register both users")
            self._register_user(driver, server, user1_data)
            self._register_user(driver, server, user2_data)
            
            # Step 2: User2 creates group and subject
            print("\n📍 Step 2: User2 creates group and subject")
            self._logout(driver, server)
            self._login(driver, server, user2_data)
            self._create_group(driver, server, group_name)
            self._navigate_to_group(driver, group_name)
            self._create_subject(driver, subject_name)
            
            # Step 3: User2 sends invitation to User1
            print("\n📍 Step 3: User2 sends invitation to User1")
            self._send_invitation(driver, user1_data["username"])
            
            # Step 4: User2 creates flashcards
            print("\n📍 Step 4: User2 creates flashcards in subject")
            self._navigate_to_subject(driver, subject_name)
            self._create_flashcards(driver)
            
            # Step 5: User2 logs out, User1 logs in
            print("\n📍 Step 5: Switch to User1")
            self._logout(driver, server)
            self._login(driver, server, user1_data)
            
            # Step 6: User1 checks and accepts invitation
            print("\n📍 Step 6: User1 checks and accepts invitation")
            
            # Wait for invitation to appear
            invitation_found = self._wait_for_invitation(driver, server, group_name, timeout=30)
            
            if invitation_found:
                print("🎉 Invitation found!")
                self._accept_invitation(driver)
            else:
                raise Exception("No invitation found for User1")
            
            # Step 7: User1 navigates to group and subject
            print("\n📍 Step 7: User1 checks flashcards")
            self._navigate_to_group(driver, group_name)
            self._navigate_to_subject(driver, subject_name)
            
            # Step 8: Verify flashcards are visible
            print("\n📍 Step 8: Verify flashcards are visible")
            time.sleep(2)
            
            # Check for flashcard accordion items
            flashcard_items = driver.find_elements(By.CSS_SELECTOR, ".MuiAccordion-root")
            # Subtract 1 for the "Frage hinzufügen" accordion
            actual_flashcard_count = len(flashcard_items) - 1
            
            assert actual_flashcard_count == 3, f"Expected 3 flashcards, found {actual_flashcard_count}"
            
            # Verify flashcard content is visible
            page_text = driver.find_element(By.TAG_NAME, "body").text
            assert "Was ist die Hauptstadt von Deutschland?" in page_text
            assert "Welche Farbe hat der Himmel?" in page_text
            assert "Wie viele Tage hat eine Woche?" in page_text
            
            print("✅ Test passed: All flashcards visible to second user")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise
    
    def test_flashcard_validation(self, driver, server, clean_database):
        """Test flashcard validation (empty fields, etc.)"""
        print("\n🎬 Starting test: Flashcard validation")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user_data = {
            "username": f"testuser{timestamp}",
            "email": f"testuser_{timestamp}@test.com",
            "password": "password123"
        }
        group_name = f"TestGroup{timestamp}"
        subject_name = f"TestSubject{timestamp}"
        
        try:
            # Setup
            self._register_user(driver, server, user_data)
            self._create_group(driver, server, group_name)
            self._navigate_to_group(driver, group_name)
            self._create_subject(driver, subject_name)
            self._navigate_to_subject(driver, subject_name)
            
            # Open flashcard form
            add_question_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Frage hinzufügen')]"))
            )
            add_question_button.click()
            time.sleep(1)
            
            # Test 1: Try to save with empty question
            print("🔍 Testing empty question validation...")
            save_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Karteikarte speichern')]")
            save_button.click()
            time.sleep(1)
            
            # Should show alert
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                print(f"✅ Alert shown: {alert_text}")
                assert "Bitte geben Sie eine Frage ein" in alert_text
                alert.accept()
                print("✅ Empty question validation works")
            except:
                # If no alert, check if card was not saved
                flashcard_count = len(driver.find_elements(By.CSS_SELECTOR, ".MuiAccordion-root")) - 1
                assert flashcard_count == 0, "Flashcard should not be saved with empty question"
                print("✅ Empty question validation works (no save)")
            
            # Test 2: Try with question but missing answers
            print("🔍 Testing incomplete answers validation...")
            question_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Geben Sie hier die Frage ein']")
            question_input.clear()
            question_input.send_keys("Test Question")
            
            # Fill only 2 answers
            answer_inputs = driver.find_elements(By.XPATH, "//input[starts-with(@placeholder, 'Antwort')]")
            answer_inputs[0].send_keys("Answer 1")
            answer_inputs[1].send_keys("Answer 2")
            
            save_button.click()
            time.sleep(1)
            
            # Should show alert or not save
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                print(f"✅ Alert shown: {alert_text}")
                alert.accept()
                print("✅ Incomplete answers validation works")
            except:
                # If no alert, check if card was not saved
                flashcard_count = len(driver.find_elements(By.CSS_SELECTOR, ".MuiAccordion-root")) - 1
                assert flashcard_count == 0, "Flashcard should not be saved with incomplete answers"
                print("✅ Incomplete answers validation works (no save)")
            
            print("✅ Test passed: Flashcard validation working correctly")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise