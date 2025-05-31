import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

class TestLoginTiming:
    """Test login timing issues"""
    
    def test_login_timing_debug(self, driver, server, clean_database):
        """Debug login timing issues"""
        # First register a user
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user_data = {"username": f"testuser{timestamp}", "email": f"test{timestamp}@example.com", "password": "testpass123"}
        
        print(f"\n🔍 LOGIN TIMING DEBUG TEST")
        print(f"👤 User: {user_data['username']}")
        
        # Register user first
        print("📍 Registering user...")
        start_time = time.time()
        driver.get(f"{server}/register")
        print(f"  ⏱️ Page load: {time.time() - start_time:.2f}s")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        
        driver.find_element(By.NAME, "username").send_keys(user_data["username"])
        driver.find_element(By.NAME, "email").send_keys(user_data["email"])
        driver.find_element(By.NAME, "password").send_keys(user_data["password"])
        driver.find_element(By.NAME, "confirmPassword").send_keys(user_data["password"])
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(driver, 10).until(EC.url_contains("/groups"))
        print(f"✅ Registration complete in {time.time() - start_time:.2f}s")
        
        # Now logout and test login timing
        print("\n📍 Logging out...")
        driver.delete_all_cookies()
        driver.get(f"{server}")
        
        # MEASURE EACH STEP OF LOGIN
        print("\n📍 LOGIN TIMING ANALYSIS:")
        
        # Step 1: Navigate to login page
        login_start = time.time()
        print(f"1️⃣ Navigate to login page...")
        driver.get(f"{server}")
        print(f"   ⏱️ Page load: {time.time() - login_start:.2f}s")
        
        # Step 2: Wait for form to appear
        form_start = time.time()
        print(f"2️⃣ Waiting for login form...")
        username_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Benutzername']"))
        )
        print(f"   ⏱️ Form appeared after: {time.time() - form_start:.2f}s")
        
        # Step 3: Find other elements
        elements_start = time.time()
        print(f"3️⃣ Finding form elements...")
        password_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Passwort']")
        submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Anmelden')]")
        print(f"   ⏱️ Elements found in: {time.time() - elements_start:.2f}s")
        
        # Step 4: Clear and fill username
        fill_start = time.time()
        print(f"4️⃣ Filling username...")
        username_field.clear()
        username_field.send_keys(user_data["username"])
        print(f"   ⏱️ Username filled in: {time.time() - fill_start:.2f}s")
        
        # Step 5: Fill password
        pass_start = time.time()
        print(f"5️⃣ Filling password...")
        password_field.clear()
        password_field.send_keys(user_data["password"])
        print(f"   ⏱️ Password filled in: {time.time() - pass_start:.2f}s")
        
        # Step 6: Click submit
        click_start = time.time()
        print(f"6️⃣ Clicking submit button...")
        submit_button.click()
        print(f"   ⏱️ Button clicked after: {time.time() - click_start:.2f}s")
        
        # Step 7: Wait for redirect
        redirect_start = time.time()
        print(f"7️⃣ Waiting for redirect to /groups...")
        WebDriverWait(driver, 30).until(EC.url_contains("/groups"))
        print(f"   ⏱️ Redirected after: {time.time() - redirect_start:.2f}s")
        
        total_time = time.time() - login_start
        print(f"\n✅ TOTAL LOGIN TIME: {total_time:.2f}s")
        
        if total_time > 10:
            print(f"⚠️  Login took longer than 10 seconds!")
        else:
            print(f"✅ Login completed within reasonable time")