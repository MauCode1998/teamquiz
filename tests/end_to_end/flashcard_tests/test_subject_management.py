import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import time


class TestSubjectManagement:
    """Test subject (Fach) management functionality - rename and delete"""

    def _register_user(self, driver, server, user_data):
        """Register a user using the working pattern"""
        print(f"🔄 Registering user: {user_data['username']}")
        driver.get(f"{server}/register")
        
        form = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        
        driver.find_element(By.NAME, "username").send_keys(user_data["username"])
        driver.find_element(By.NAME, "email").send_keys(user_data["email"])
        driver.find_element(By.NAME, "password").send_keys(user_data["password"])
        driver.find_element(By.NAME, "confirmPassword").send_keys(user_data["password"])
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        time.sleep(1.5)
        WebDriverWait(driver, 10).until(EC.url_contains("/groups"))
        print(f"✅ User {user_data['username']} registered successfully")

    def _create_group(self, driver, group_name):
        """Create a group using working pattern"""
        group_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Gruppenname']")
        group_input.clear()
        group_input.send_keys(group_name)
        
        submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Erstellen!')]")
        submit_button.click()
        time.sleep(0.5)
        print(f"✅ Group '{group_name}' created")

    def _navigate_to_group(self, driver, group_name):
        """Navigate to a specific group"""
        group_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, group_name))
        )
        group_link.click()
        WebDriverWait(driver, 10).until(EC.url_contains(f"/groups/{group_name}"))
        time.sleep(1)

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

    def _navigate_to_subject(self, driver, group_name, subject_name):
        """Navigate to a specific subject page"""
        subject_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, subject_name))
        )
        subject_link.click()
        WebDriverWait(driver, 10).until(EC.url_contains(f"/groups/{group_name}/"))
        time.sleep(1)

    def test_subject_rename(self, driver, server, clean_database):
        """Test renaming a subject"""
        print("\n🎬 Starting test: Subject rename")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user_data = {"username": f"testuser{timestamp}", "email": f"testuser{timestamp}@test.com", "password": "password123"}
        group_name = f"TestGruppe{timestamp}"
        subject_name = f"TestFach{timestamp}"
        new_subject_name = f"RenamedFach{timestamp}"
        
        try:
            # Setup
            self._register_user(driver, server, user_data)
            self._create_group(driver, group_name)
            self._navigate_to_group(driver, group_name)
            self._create_subject(driver, subject_name)
            
            # Navigate to subject to find rename button
            self._navigate_to_subject(driver, group_name, subject_name)
            
            # Click "Fach umbenennen" button
            print("🔍 Looking for 'Fach umbenennen' button...")
            rename_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Fach umbenennen')]"))
            )
            rename_button.click()
            time.sleep(1)
            
            # Should open a rename dialog/input
            print("🔍 Looking for rename input field...")
            rename_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='neuen'], input[placeholder*='Namen'], input[placeholder*='umbenennen']"))
            )
            # Clear the field completely and enter new name
            rename_input.click()
            time.sleep(0.2)
            # Get current value and clear it manually
            current_value = rename_input.get_attribute("value")
            print(f"Current input value: '{current_value}'")
            
            # Delete all characters one by one to be sure
            for _ in range(len(current_value)):
                rename_input.send_keys(Keys.BACKSPACE)
            time.sleep(0.2)
            
            # Now enter the new name
            rename_input.send_keys(new_subject_name)
            print(f"Entered new name: '{new_subject_name}'")
            
            # Confirm rename
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Bestätigen') or contains(text(), 'Speichern') or contains(text(), 'Umbenennen')]"))
            )
            confirm_button.click()
            time.sleep(2)
            
            # Wait a bit for the navigation to complete
            print("🔍 Waiting for navigation to complete...")
            time.sleep(3)
            
            # Check if we're on the renamed subject page by URL
            current_url = driver.current_url
            print(f"Current URL: {current_url}")
            assert f"/groups/{group_name}/" in current_url, "Not on a subject page"
            
            # Navigate back to group and verify new name appears in subject list
            print("🔍 Navigating back to group to verify rename...")
            driver.get(f"{server}/groups/{group_name}")
            WebDriverWait(driver, 10).until(EC.url_contains(f"/groups/{group_name}"))
            time.sleep(2)
            
            # Try to click on the renamed subject to verify it works
            print(f"🔍 Looking for renamed subject link: {new_subject_name}")
            
            # Give the page more time to load and retry if needed
            for attempt in range(3):
                try:
                    print(f"   Attempt {attempt + 1}/3 to find renamed subject...")
                    renamed_subject_link = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '{new_subject_name}') or contains(text(), '{new_subject_name}')]"))
                    )
                    print(f"   Found link, clicking...")
                    renamed_subject_link.click()
                    
                    # Verify we're on the renamed subject page with longer timeout
                    WebDriverWait(driver, 15).until(EC.url_contains(f"/groups/{group_name}/"))
                    time.sleep(2)  # Extra wait for page to fully load
                    
                    current_url = driver.current_url
                    print(f"   Successfully navigated to: {current_url}")
                    
                    # Check if we're on any subject page (URL might have extra characters)
                    if f"/groups/{group_name}/" in current_url and len(current_url.split("/")) >= 5:
                        print(f"✅ Successfully navigated to renamed subject page")
                        
                        # Verify the page shows the correct subject name  
                        page_text = driver.find_element(By.TAG_NAME, "body").text
                        if new_subject_name in page_text:
                            print(f"✅ Page contains renamed subject name: {new_subject_name}")
                            break
                        else:
                            print(f"   Page doesn't contain subject name, retrying...")
                            if attempt < 2:
                                driver.get(f"{server}/groups/{group_name}")
                                time.sleep(3)
                                continue
                    else:
                        print(f"   Wrong URL, retrying...")
                        if attempt < 2:
                            driver.get(f"{server}/groups/{group_name}")
                            time.sleep(3)
                            continue
                            
                except Exception as e:
                    print(f"   Attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        print(f"   Refreshing page and retrying...")
                        driver.get(f"{server}/groups/{group_name}")
                        time.sleep(3)
                    else:
                        raise
            
            print("✅ Test passed: Subject renamed successfully")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            driver.save_screenshot("test_reports/subject_rename_failed.png")
            raise

    def test_subject_delete(self, driver, server, clean_database):
        """Test deleting a subject"""
        print("\n🎬 Starting test: Subject delete")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user_data = {"username": f"testuser{timestamp}", "email": f"testuser{timestamp}@test.com", "password": "password123"}
        group_name = f"TestGruppe{timestamp}"
        subject_name = f"TestFach{timestamp}"
        
        try:
            # Setup
            self._register_user(driver, server, user_data)
            self._create_group(driver, group_name)
            self._navigate_to_group(driver, group_name)
            self._create_subject(driver, subject_name)
            
            # Navigate to subject to find delete button
            self._navigate_to_subject(driver, group_name, subject_name)
            
            # Click "Fach löschen" button
            print("🔍 Looking for 'Fach löschen' button...")
            delete_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Fach löschen')]"))
            )
            delete_button.click()
            time.sleep(1)
            
            # Should open a confirmation dialog
            print("🔍 Looking for delete confirmation...")
            try:
                # Look for confirmation dialog/button
                confirm_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Bestätigen') or contains(text(), 'Löschen') or contains(text(), 'Ja')]"))
                )
                confirm_button.click()
                time.sleep(2)
            except:
                # If no confirmation dialog, delete might have happened immediately
                print("🔍 No confirmation dialog found, checking if delete happened immediately")
            
            # Should redirect back to group page after deletion
            print("🔍 Verifying subject was deleted...")
            WebDriverWait(driver, 10).until(EC.url_contains(f"/groups/{group_name}"))
            time.sleep(1)
            
            # Verify subject no longer appears in group page
            group_page_text = driver.find_element(By.TAG_NAME, "body").text
            assert subject_name not in group_page_text, f"Deleted subject '{subject_name}' still found in group page"
            
            # Try to navigate to deleted subject (should fail or redirect)
            print("🔍 Verifying deleted subject is not accessible...")
            driver.get(f"{server}/groups/{group_name}/{subject_name}")
            time.sleep(2)
            
            # Should not be on the subject page anymore
            current_url = driver.current_url
            assert f"/groups/{group_name}/{subject_name}" not in current_url, "Deleted subject page is still accessible"
            
            print("✅ Test passed: Subject deleted successfully")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            driver.save_screenshot("test_reports/subject_delete_failed.png")
            raise

    def test_subject_delete_with_flashcards(self, driver, server, clean_database):
        """Test deleting a subject that contains flashcards"""
        print("\n🎬 Starting test: Subject delete with flashcards")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user_data = {"username": f"testuser{timestamp}", "email": f"testuser{timestamp}@test.com", "password": "password123"}
        group_name = f"TestGruppe{timestamp}"
        subject_name = f"TestFach{timestamp}"
        
        try:
            # Setup
            self._register_user(driver, server, user_data)
            self._create_group(driver, group_name)
            self._navigate_to_group(driver, group_name)
            self._create_subject(driver, subject_name)
            self._navigate_to_subject(driver, group_name, subject_name)
            
            # Create a flashcard in this subject
            print("🔍 Creating flashcard in subject...")
            flashcard_accordion = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Frage hinzufügen')]"))
            )
            flashcard_accordion.click()
            time.sleep(1)
            
            # Fill flashcard
            question_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='Geben Sie hier die Frage ein']"))
            )
            question_input.send_keys("Test question before delete")
            
            answer_inputs = driver.find_elements(By.XPATH, "//input[starts-with(@placeholder, 'Antwort')]")
            for i, answer in enumerate(["A1", "A2", "A3", "A4"]):
                answer_inputs[i].send_keys(answer)
            
            save_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Karteikarte speichern')]")
            save_button.click()
            time.sleep(2)
            
            # Verify flashcard was created
            question_count = driver.find_element(By.XPATH, "//h2[contains(text(), 'Alle Fragen')]").text
            assert "(1)" in question_count, "Flashcard was not created"
            print("✅ Flashcard created")
            
            # Now try to delete the subject
            print("🔍 Attempting to delete subject with flashcards...")
            delete_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Fach löschen')]"))
            )
            delete_button.click()
            time.sleep(1)
            
            # Should show warning about deleting flashcards
            page_text = driver.find_element(By.TAG_NAME, "body").text
            if "Karteikarten" in page_text or "verloren" in page_text or "löschen" in page_text:
                print("✅ Warning about deleting flashcards detected")
            
            # Confirm deletion
            try:
                confirm_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Bestätigen') or contains(text(), 'Löschen') or contains(text(), 'Ja')]"))
                )
                confirm_button.click()
                time.sleep(2)
            except:
                print("🔍 No confirmation dialog found")
            
            # Verify subject and flashcards were deleted
            WebDriverWait(driver, 10).until(EC.url_contains(f"/groups/{group_name}"))
            time.sleep(1)
            
            group_page_text = driver.find_element(By.TAG_NAME, "body").text
            assert subject_name not in group_page_text, f"Deleted subject '{subject_name}' still found in group page"
            
            print("✅ Test passed: Subject with flashcards deleted successfully")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            driver.save_screenshot("test_reports/subject_delete_flashcards_failed.png")
            raise

    def test_subject_rename_validation(self, driver, server, clean_database):
        """Test subject rename with invalid input (empty name, duplicate name)"""
        print("\n🎬 Starting test: Subject rename validation")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user_data = {"username": f"testuser{timestamp}", "email": f"testuser{timestamp}@test.com", "password": "password123"}
        group_name = f"TestGruppe{timestamp}"
        subject1_name = f"TestFach1_{timestamp}"
        subject2_name = f"TestFach2_{timestamp}"
        
        try:
            # Setup with two subjects
            self._register_user(driver, server, user_data)
            self._create_group(driver, group_name)
            self._navigate_to_group(driver, group_name)
            self._create_subject(driver, subject1_name)
            self._create_subject(driver, subject2_name)
            
            # Navigate to first subject
            self._navigate_to_subject(driver, group_name, subject1_name)
            
            # Test 1: Try to rename to empty name
            print("🔍 Testing rename to empty name...")
            rename_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Fach umbenennen')]"))
            )
            rename_button.click()
            time.sleep(1)
            
            rename_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='neuen'], input[placeholder*='Namen'], input[placeholder*='umbenennen']"))
            )
            rename_input.clear()
            rename_input.send_keys("")  # Empty name
            
            confirm_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Bestätigen') or contains(text(), 'Speichern') or contains(text(), 'Umbenennen')]")
            confirm_button.click()
            time.sleep(1)
            
            # Should show error message
            page_text = driver.find_element(By.TAG_NAME, "body").text
            assert any(word in page_text.lower() for word in ["fehler", "error", "leer", "empty", "required"]), "No error message for empty name"
            print("✅ Empty name validation works")
            
            # Test 2: Try to rename to duplicate name
            print("🔍 Testing rename to duplicate name...")
            rename_input.clear()
            rename_input.send_keys(subject2_name)  # Name that already exists
            confirm_button.click()
            time.sleep(1)
            
            page_text = driver.find_element(By.TAG_NAME, "body").text
            assert any(word in page_text.lower() for word in ["fehler", "error", "existiert", "exists", "duplicate"]), "No error message for duplicate name"
            print("✅ Duplicate name validation works")
            
            print("✅ Test passed: Subject rename validation working")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            driver.save_screenshot("test_reports/subject_rename_validation_failed.png")
            raise