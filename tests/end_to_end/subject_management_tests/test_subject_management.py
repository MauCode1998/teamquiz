import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import time
from tests.utils.ui_helpers import create_subject_ui, wait_for_groups_page, wait_for_group_page
from tests.utils.test_data import generate_test_user, generate_test_group, generate_test_subject


class TestSubjectManagement:
    """Test subject (Fach) management functionality - rename and delete - REFACTORED"""

    def test_subject_rename_optimized(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login,
        login_user_ui, navigate_to_group
    ):
        """Test renaming a subject - OPTIMIZED VERSION"""
        print("\n🎬 Starting OPTIMIZED test: Subject rename")
        
        # Fast setup with API calls
        user_data = generate_test_user()
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        new_subject_name = f"Renamed{subject_name}"
        
        api_create_user(user_data["username"], user_data["email"], user_data["password"])
        auth_data = api_login(user_data["username"], user_data["password"])
        api_create_group(group_name, auth_data)
        api_create_subject(subject_name, group_name, auth_data)
        
        print(f"✅ FAST SETUP: User, group, and subject created via API")
        
        try:
            # Test only the rename UI functionality
            login_user_ui(user_data["username"], user_data["password"])
            navigate_to_group(group_name)
            
            # Navigate to subject
            driver.get(f"{server}/groups/{group_name}/{subject_name}")
            wait_for_group_page(driver, group_name)
            
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
            
            # Clear and enter new name
            rename_input.click()
            time.sleep(0.2)
            current_value = rename_input.get_attribute("value")
            print(f"Current input value: '{current_value}'")
            
            # Delete all characters
            for _ in range(len(current_value)):
                rename_input.send_keys(Keys.BACKSPACE)
            time.sleep(0.2)
            
            # Enter new name
            rename_input.send_keys(new_subject_name)
            print(f"Entered new name: '{new_subject_name}'")
            
            # Confirm rename
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Bestätigen') or contains(text(), 'Speichern') or contains(text(), 'Umbenennen')]"))
            )
            confirm_button.click()
            time.sleep(2)
            
            # Verify rename worked
            print("🔍 Verifying rename worked...")
            driver.get(f"{server}/groups/{group_name}")
            time.sleep(2)
            
            # Look for renamed subject
            page_text = driver.find_element(By.TAG_NAME, "body").text
            assert new_subject_name in page_text, f"Renamed subject '{new_subject_name}' not found"
            
            print("✅ OPTIMIZED Test passed: Subject renamed successfully")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            driver.save_screenshot("test_reports/subject_rename_failed.png")
            raise

    def test_subject_delete_optimized(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login,
        login_user_ui, navigate_to_group
    ):
        """Test deleting a subject - OPTIMIZED VERSION"""
        print("\n🎬 Starting OPTIMIZED test: Subject delete")
        
        # Fast setup with API calls (uses test database automatically)
        user_data = generate_test_user()
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        
        # Create user via API
        api_create_user(user_data["username"], user_data["email"], user_data["password"])
        
        # Login to get auth data  
        auth_data = api_login(user_data["username"], user_data["password"])
        
        # Create group and subject via API  
        api_create_group(group_name, auth_data)
        api_create_subject(subject_name, group_name, auth_data)
        
        print(f"✅ FAST SETUP: User, group, and subject created via API")
        
        try:
            # Test only the delete UI functionality
            login_user_ui(user_data["username"], user_data["password"])
            navigate_to_group(group_name)
            
            # Navigate to subject
            driver.get(f"{server}/groups/{group_name}/{subject_name}")
            wait_for_group_page(driver, group_name)
            
            # Click "Fach löschen" button
            print("🔍 Looking for 'Fach löschen' button...")
            delete_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Fach löschen')]"))
            )
            delete_button.click()
            time.sleep(1)
            
            # Confirm deletion if dialog appears
            try:
                confirm_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Bestätigen') or contains(text(), 'Löschen') or contains(text(), 'Ja')]"))
                )
                confirm_button.click()
                time.sleep(0.5)
            except:
                print("🔍 No confirmation dialog found")
            
            # Verify subject was deleted
            print("🔍 Verifying subject was deleted...")
            WebDriverWait(driver, 3).until(EC.url_contains(f"/groups/{group_name}"))
            time.sleep(0.5)
            
            group_page_text = driver.find_element(By.TAG_NAME, "body").text
            assert subject_name not in group_page_text, f"Deleted subject '{subject_name}' still found"
            
            print("✅ OPTIMIZED Test passed: Subject deleted successfully")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            driver.save_screenshot("test_reports/subject_delete_failed.png")
            raise

    def test_subject_delete_with_flashcards_optimized(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login,
        login_user_ui, navigate_to_group
    ):
        """Test deleting a subject that contains flashcards - OPTIMIZED VERSION"""
        print("\n🎬 Starting OPTIMIZED test: Subject delete with flashcards")
        
        # Fast setup with API calls
        user_data = generate_test_user()
        group_name = generate_test_group()
        subject_name = generate_test_subject()
        
        api_create_user(user_data["username"], user_data["email"], user_data["password"])
        auth_data = api_login(user_data["username"], user_data["password"])
        api_create_group(group_name, auth_data)
        api_create_subject(subject_name, group_name, auth_data)
        
        print(f"✅ FAST SETUP: User, group, and subject created via API")
        
        try:
            # Test only the UI functionality
            login_user_ui(user_data["username"], user_data["password"])
            navigate_to_group(group_name)
            
            # Navigate to subject
            driver.get(f"{server}/groups/{group_name}/{subject_name}")
            wait_for_group_page(driver, group_name)
            
            # Create a flashcard first
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
            
            # Select correct answer
            radio_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            radio_buttons[0].click()
            
            save_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Karteikarte speichern')]")
            save_button.click()
            time.sleep(2)
            
            print("✅ Flashcard created")
            
            # Now try to delete the subject
            print("🔍 Attempting to delete subject with flashcards...")
            delete_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Fach löschen')]"))
            )
            delete_button.click()
            time.sleep(1)
            
            # Confirm deletion
            try:
                confirm_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "fachLoeschenButton")
                ))
                confirm_button.click()
                time.sleep(0.5)
            except:
                print("🔍 No confirmation dialog found")
            
            # Verify subject and flashcards were deleted
            WebDriverWait(driver, 3).until(EC.url_contains(f"/groups/{group_name}"))
            time.sleep(0.5)
            
            group_page_text = driver.find_element(By.TAG_NAME, "body").text
            assert subject_name not in group_page_text, f"Deleted subject '{subject_name}' still found"
            
            print("✅ OPTIMIZED Test passed: Subject with flashcards deleted successfully")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            driver.save_screenshot("test_reports/subject_delete_flashcards_failed.png")
            raise

    def test_subject_rename_validation_optimized(
        self, driver, server, clean_database,
        api_create_user, api_create_group, api_create_subject, api_login,
        login_user_ui, navigate_to_group
    ):
        """Test subject rename with invalid input - OPTIMIZED VERSION"""
        print("\n🎬 Starting OPTIMIZED test: Subject rename validation")
        
        # Fast setup with API calls
        user_data = generate_test_user()
        group_name = generate_test_group()
        subject1_name = generate_test_subject("Subject1")
        subject2_name = generate_test_subject("Subject2")
        
        api_create_user(user_data["username"], user_data["email"], user_data["password"])
        auth_data = api_login(user_data["username"], user_data["password"])
        api_create_group(group_name, auth_data)
        api_create_subject(subject1_name, group_name, auth_data)
        api_create_subject(subject2_name, group_name, auth_data)
        
        print(f"✅ FAST SETUP: User, group, and 2 subjects created via API")
        
        try:
            # Test only the validation UI functionality
            login_user_ui(user_data["username"], user_data["password"])
            navigate_to_group(group_name)
            
            # Navigate to first subject
            driver.get(f"{server}/groups/{group_name}/{subject1_name}")
            wait_for_group_page(driver, group_name)
            
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
            
            print("✅ OPTIMIZED Test passed: Subject rename validation working")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            driver.save_screenshot("test_reports/subject_rename_validation_failed.png")
            raise