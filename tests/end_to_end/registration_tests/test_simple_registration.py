import pytest
import requests
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime

class TestSimpleRegistration:
    """Simple registration tests without complex server setup"""
    
    def test_check_safari_driver(self, driver):
        """Simple test to verify Safari driver works"""
        driver.get("https://google.com")
        assert "Google" in driver.title
    
    def test_check_server_health(self, server):
        """Test if single server is accessible"""
        response = requests.get(server, timeout=5)
        # Server should respond (might be 200 for React app or 404/422 for API)
        assert response.status_code in [200, 404, 422]
    
    def test_frontend_registration_form_elements(self, driver, server):
        """Test if registration form has required elements"""
        driver.get(f"{server}/register")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        
        # Check for required form fields
        username_field = driver.find_element(By.NAME, "username")
        email_field = driver.find_element(By.NAME, "email") 
        password_field = driver.find_element(By.NAME, "password")
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        assert username_field.is_displayed()
        assert email_field.is_displayed()
        assert password_field.is_displayed()
        assert submit_button.is_displayed()
    
    def test_backend_register_endpoint_directly(self, server, clean_database):
        """Test backend registration endpoint directly"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Test with valid data (unique username)
        response = requests.post(f"{server}/register", json={
            "username": f"testuser{timestamp}",
            "email": f"test{timestamp}@example.com", 
            "password": "password123"
        }, timeout=5)
        
        # Should succeed with 200
        assert response.status_code == 200
        assert "access_token" in response.json()
        
        # Test with invalid data (missing fields)
        response = requests.post(f"{server}/register", json={
            "username": "incomplete"
        }, timeout=5)
        
        assert response.status_code == 422  # Validation error
    
    def test_complete_registration_flow(self, driver, server, clean_database):
        """Test complete registration flow from start to finish"""
        # Generate unique username with timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_data = {"username": f"testuser{timestamp}", "email": f"testuser{timestamp}@example.com", "password": "testpass123"}
        
        print(f"\n🎬 Starting registration test for user: {test_data['username']}")
        
        # Step 1: Navigate to registration page
        print("📍 Step 1: Navigate to registration page")
        driver.get(f"{server}/register")
        
        # Step 2: Check if registration form exists
        print("📍 Step 2: Locate registration form")
        try:
            # Wait for form to load
            form = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "form"))
            )
            
            # Find form fields
            username_field = driver.find_element(By.NAME, "username")
            email_field = driver.find_element(By.NAME, "email")
            password_field = driver.find_element(By.NAME, "password")
            confirm_password_field = driver.find_element(By.NAME, "confirmPassword")
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            
            print("✅ Registration form found with all required fields")
            
        except Exception as e:
            print(f"❌ Could not find registration form: {e}")
            # Take screenshot for debugging
            driver.save_screenshot("test_reports/registration_form_error.png")
            raise
        
        # Step 3: Fill out registration form
        print("📍 Step 3: Fill out registration form")
        username_field.clear()
        username_field.send_keys(test_data["username"])
        
        email_field.clear()
        email_field.send_keys(test_data["email"])
        
        password_field.clear()
        password_field.send_keys(test_data["password"])
        
        confirm_password_field.clear()
        confirm_password_field.send_keys(test_data["password"])
        
        print(f"✅ Form filled with: {test_data['username']}, {test_data['email']}")
        
        # Step 4: Submit registration
        print("📍 Step 4: Submit registration")
        submit_button.click()
        time.sleep(1.5)  # Wait for redirect after successful registration
        
        # Step 5: Check if registration was successful
        print("📍 Step 5: Verify registration success")
        
        # Check current URL (should redirect away from /register if successful)
        current_url = driver.current_url
        print(f"Current URL after submission: {current_url}")
        
        # Method 1: Check if redirected (successful registration usually redirects)
        success_indicators = [
            "/login" in current_url.lower(),
            "/groups" in current_url.lower(),
            "/dashboard" in current_url.lower(),
            current_url != f"{server}/register"
        ]
        
        # Step 6: Verify overall success based on redirect
        if any(success_indicators):
            print("🎉 REGISTRATION TEST PASSED!")
            print(f"✅ Successfully redirected to: {current_url}")
            assert True
        else:
            print("💥 REGISTRATION TEST FAILED!")
            # Take screenshot for debugging
            driver.save_screenshot("test_reports/registration_failed.png")
            assert False, "Registration was not successful"