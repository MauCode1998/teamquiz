import pytest
import requests
import time
import sqlite3
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime

class TestRegistrationValidation:
    """Test registration form validation and error handling"""
    
    def test_duplicate_username_shows_error(self, driver, server, clean_database):
        """Test that registering same username twice shows appropriate error"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_data = {
            "username": f"duplicate{timestamp}", 
            "email": f"duplicate{timestamp}@example.com", 
            "password": "testpass123"
        }
        
        print(f"\n🎬 Testing duplicate username: {test_data['username']}")
        
        # First registration - should succeed
        print("📍 Step 1: First registration (should succeed)")
        driver.get(f"{server}/register")
        time.sleep(0.5)
        
        self._fill_registration_form(driver, test_data)
        self._submit_form(driver)
        time.sleep(0.5)
        
        # Should redirect to /groups
        current_url = driver.current_url
        if "/groups" in current_url:
            print("✅ First registration successful")
        else:
            print(f"⚠️ First registration may have failed. URL: {current_url}")
        
        # Second registration - should fail with error
        print("📍 Step 2: Second registration (should fail)")
        driver.get(f"{server}/register")
        time.sleep(0.5)
        
        self._fill_registration_form(driver, test_data)
        self._submit_form(driver)
        time.sleep(0.5)
        
        # Should stay on register page with error message
        current_url = driver.current_url
        error_message = self._get_error_message(driver)
        
        if "/register" in current_url and error_message:
            print(f"✅ Duplicate username correctly rejected: {error_message}")
            assert "bereits registriert" in error_message.lower() or "already registered" in error_message.lower()
        else:
            print("❌ Duplicate username was not properly rejected")
            driver.save_screenshot("test_reports/duplicate_username_failed.png")
            assert False, f"Expected error for duplicate username. URL: {current_url}, Error: {error_message}"
    
    def test_underscore_in_username(self, driver, server, clean_database):
        """Test username with underscore - should either work or show clear error"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_data = {
            "username": f"test_user_{timestamp}", 
            "email": f"testuser{timestamp}@example.com", 
            "password": "testpass123"
        }
        
        print(f"\n🎬 Testing underscore username: {test_data['username']}")
        
        driver.get(f"{server}/register")
        time.sleep(0.5)
        
        self._fill_registration_form(driver, test_data)
        self._submit_form(driver)
        time.sleep(0.3)
        
        # Check if page went blank (white screen)
        page_source = driver.page_source
        print(f"Page length after submit: {len(page_source)} characters")
        if len(page_source) < 1000:  # Very short page = likely blank
            print("⚠️ Page appears to be blank/white after submission")
            driver.save_screenshot("test_reports/underscore_blank_page.png")
        
        current_url = driver.current_url
        error_message = self._get_error_message(driver)
        
        # Check browser console for JavaScript errors
        try:
            console_logs = driver.get_log('browser')
            if console_logs:
                print("🔍 Browser console errors:")
                for log in console_logs:
                    print(f"  {log['level']}: {log['message']}")
        except:
            print("ℹ️ Cannot access browser console logs")
        
        # Check if form fields still have values (indicating form wasn't submitted)
        try:
            username_field = driver.find_element(By.NAME, "username")
            current_username = username_field.get_attribute('value')
            print(f"🔍 Username field still contains: '{current_username}'")
        except:
            pass
        
        if "/groups" in current_url:
            print("✅ Username with underscore accepted")
            assert True
        elif error_message and ("buchstaben und zahlen" in error_message.lower() or "letters and numbers" in error_message):
            print(f"✅ Clear error message for underscore: {error_message}")
            assert True
        else:
            print(f"❌ Underscore handling unclear. URL: {current_url}, Error: {error_message}")
            driver.save_screenshot("test_reports/underscore_username_unclear.png")
            assert False, f"Expected clear error message for underscore. Got: {error_message}"
    
    def test_missing_username_field(self, driver, server, clean_database):
        """Test submitting form without username"""
        print("\n🎬 Testing missing username field")
        
        driver.get(f"{server}/register")
        time.sleep(0.5)
        
        # Fill form but leave username empty
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        confirm_password_field = driver.find_element(By.NAME, "confirmPassword")
        
        email_field.send_keys("test@example.com")
        password_field.send_keys("testpass123")
        confirm_password_field.send_keys("testpass123")
        
        self._submit_form(driver)
        time.sleep(0.5)
        
        # Should stay on register page
        current_url = driver.current_url
        error_message = self._get_error_message(driver)
        
        if "/register" in current_url:
            print("✅ Form submission blocked without username")
            if error_message:
                print(f"✅ Error message shown: {error_message}")
                # Check for German error message
                assert "benutzername ist erforderlich" in error_message.lower() or "erforderlich" in error_message.lower()
            else:
                assert True  # Browser validation might prevent submission
        else:
            print("❌ Form was submitted without username")
            assert False, "Form should not submit without username"
    
    def test_missing_email_field(self, driver, server, clean_database):
        """Test submitting form without email"""
        print("\n🎬 Testing missing email field")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        driver.get(f"{server}/register")
        time.sleep(0.5)
        
        # Fill form but leave email empty
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")
        confirm_password_field = driver.find_element(By.NAME, "confirmPassword")
        
        username_field.send_keys(f"testuser{timestamp}")
        password_field.send_keys("testpass123")
        confirm_password_field.send_keys("testpass123")
        
        self._submit_form(driver)
        time.sleep(0.5)
        
        # Should stay on register page
        current_url = driver.current_url
        error_message = self._get_error_message(driver)
        
        if "/register" in current_url:
            print("✅ Form submission blocked without email")
            if error_message:
                print(f"✅ Error message shown: {error_message}")
            assert True
        else:
            print("❌ Form was submitted without email")
            assert False, "Form should not submit without email"
    
    def test_missing_password_field(self, driver, server, clean_database):
        """Test submitting form without password"""
        print("\n🎬 Testing missing password field")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        driver.get(f"{server}/register")
        time.sleep(0.5)
        
        # Fill form but leave password empty
        username_field = driver.find_element(By.NAME, "username")
        email_field = driver.find_element(By.NAME, "email")
        
        username_field.send_keys(f"testuser{timestamp}")
        email_field.send_keys(f"testuser{timestamp}@example.com")
        
        self._submit_form(driver)
        time.sleep(0.5)
        
        # Should stay on register page
        current_url = driver.current_url
        error_message = self._get_error_message(driver)
        
        if "/register" in current_url:
            print("✅ Form submission blocked without password")
            if error_message:
                print(f"✅ Error message shown: {error_message}")
            assert True
        else:
            print("❌ Form was submitted without password")
            assert False, "Form should not submit without password"
    
    def test_password_mismatch(self, driver, server, clean_database):
        """Test that mismatched passwords show error"""
        print("\n🎬 Testing password mismatch")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        driver.get(f"{server}/register")
        time.sleep(0.5)
        
        # Fill form with mismatched passwords
        username_field = driver.find_element(By.NAME, "username")
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        confirm_password_field = driver.find_element(By.NAME, "confirmPassword")
        
        username_field.send_keys(f"testuser{timestamp}")
        email_field.send_keys(f"testuser{timestamp}@example.com")
        password_field.send_keys("testpass123")
        confirm_password_field.send_keys("differentpass123")  # Different password
        
        self._submit_form(driver)
        time.sleep(0.5)
        
        # Should stay on register page with error
        current_url = driver.current_url
        error_message = self._get_error_message(driver)
        
        if "/register" in current_url and error_message:
            print(f"✅ Password mismatch correctly detected: {error_message}")
            assert "stimmen nicht überein" in error_message or "match" in error_message.lower()
        else:
            print("❌ Password mismatch was not detected")
            driver.save_screenshot("test_reports/password_mismatch_failed.png")
            assert False, f"Expected error for password mismatch. URL: {current_url}, Error: {error_message}"
    
    def test_invalid_email_format(self, driver, server, clean_database):
        """Test invalid email format shows error"""
        print("\n🎬 Testing invalid email format")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_data = {
            "username": f"testuser{timestamp}", 
            "email": "invalid-email-format",  # Invalid email
            "password": "testpass123"
        }
        
        driver.get(f"{server}/register")
        time.sleep(0.5)
        
        self._fill_registration_form(driver, test_data)
        self._submit_form(driver)
        time.sleep(0.5)
        
        # Should stay on register page
        current_url = driver.current_url
        error_message = self._get_error_message(driver)
        
        if "/register" in current_url:
            print("✅ Invalid email format blocked")
            if error_message:
                print(f"✅ Error message shown: {error_message}")
            assert True
        else:
            print("❌ Invalid email format was accepted")
            assert False, "Invalid email should be rejected"
    
    def test_short_password(self, driver, server, clean_database):
        """Test that short password shows error"""
        print("\n🎬 Testing short password")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_data = {
            "username": f"testuser{timestamp}", 
            "email": f"testuser{timestamp}@example.com", 
            "password": "123"  # Too short
        }
        
        driver.get(f"{server}/register")
        time.sleep(0.5)
        
        self._fill_registration_form(driver, test_data)
        self._submit_form(driver)
        time.sleep(0.5)
        
        # Should stay on register page with error
        current_url = driver.current_url
        error_message = self._get_error_message(driver)
        
        if "/register" in current_url and error_message:
            print(f"✅ Short password correctly rejected: {error_message}")
            assert "6 zeichen" in error_message.lower() or "too short" in error_message.lower() or "mindestens" in error_message.lower()
        else:
            print("❌ Short password was not rejected")
            driver.save_screenshot("test_reports/short_password_failed.png")
            assert False, f"Expected error for short password. URL: {current_url}, Error: {error_message}"
    
    # Helper methods
    def _fill_registration_form(self, driver, test_data):
        """Fill registration form with test data"""
        username_field = driver.find_element(By.NAME, "username")
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        confirm_password_field = driver.find_element(By.NAME, "confirmPassword")
        
        username_field.clear()
        username_field.send_keys(test_data["username"])
        
        email_field.clear()
        email_field.send_keys(test_data["email"])
        
        password_field.clear()
        password_field.send_keys(test_data["password"])
        
        confirm_password_field.clear()
        confirm_password_field.send_keys(test_data["password"])
    
    def _submit_form(self, driver):
        """Submit the registration form"""
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
    
    def _get_error_message(self, driver):
        """Get error message from page if it exists"""
        try:
            error_element = driver.find_element(By.CSS_SELECTOR, "[role='alert']")
            return error_element.text if error_element else None
        except:
            return None