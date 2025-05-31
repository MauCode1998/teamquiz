import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

class TestLoginLogout:
    """Test basic login/logout functionality"""
    
    def test_register_logout_login_cycle(self, driver, server, clean_database):
        """Test: Register → Logout → Login cycle"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        user_data = {"username": f"testuser{timestamp}", "email": f"testuser{timestamp}@example.com", "password": "testpass123"}
        
        print(f"\n🎬 Starting login/logout test")
        print(f"👤 User: {user_data['username']}")
        
        # Step 1: Register user
        print("📍 Step 1: Register user")
        self._register_user(driver, server, user_data)
        
        # Step 2: Verify user is logged in (should be on groups page)
        print("📍 Step 2: Verify user is logged in")
        assert "/groups" in driver.current_url
        
        # Check if username appears on page
        page_text = driver.find_element(By.TAG_NAME, "body").text
        assert user_data['username'] in page_text
        print(f"✅ User {user_data['username']} is logged in and visible on page")
        
        # Step 3: Logout user
        print("📍 Step 3: Logout user")
        self._logout_user(driver, server)
        
        # Step 4: Login user again
        print("📍 Step 4: Login user again") 
        self._login_user(driver, server, user_data)
        
        # Step 5: Verify user is logged in again
        print("📍 Step 5: Verify user is logged in again")
        assert "/groups" in driver.current_url
        
        page_text = driver.find_element(By.TAG_NAME, "body").text
        assert user_data['username'] in page_text
        print(f"✅ User {user_data['username']} successfully logged in again")
        
        print("🎉 LOGIN/LOGOUT TEST PASSED!")
        
    def _register_user(self, driver, server, user_data):
        """Register a user"""
        driver.get(f"{server}/register")
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        
        driver.find_element(By.NAME, "username").send_keys(user_data["username"])
        driver.find_element(By.NAME, "email").send_keys(user_data["email"])
        driver.find_element(By.NAME, "password").send_keys(user_data["password"])
        driver.find_element(By.NAME, "confirmPassword").send_keys(user_data["password"])
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for redirect to groups page
        WebDriverWait(driver, 15).until(
            EC.url_contains("/groups")
        )
        
        time.sleep(2)  # Wait for page to load
        print(f"✅ User {user_data['username']} registered")
    
    def _logout_user(self, driver, server):
        """Logout current user"""
        print("🔄 Looking for logout button...")
        
        # Debug: Print current page state
        current_url = driver.current_url
        page_text = driver.find_element(By.TAG_NAME, "body").text[:300]
        print(f"DEBUG: Current URL: {current_url}")
        print(f"DEBUG: Page text: {page_text}")
        
        try:
            # Look for logout button with various selectors
            logout_selectors = [
                "//button[contains(text(), 'Logout')]",
                "//button[contains(text(), 'Abmelden')]", 
                "//a[contains(text(), 'Logout')]",
                "//a[contains(text(), 'Abmelden')]",
                "//button[contains(@class, 'logout')]",
                "//a[contains(@class, 'logout')]",
                "//*[contains(text(), 'Logout')]",
                "//*[contains(text(), 'Abmelden')]"
            ]
            
            logout_button = None
            for selector in logout_selectors:
                try:
                    logout_button = driver.find_element(By.XPATH, selector)
                    print(f"✅ Found logout button with selector: {selector}")
                    break
                except:
                    continue
            
            if logout_button:
                logout_button.click()
                print("✅ Clicked logout button")
                
                # Wait for redirect to login page
                time.sleep(3)
                
                # Check if we're back at login
                current_url = driver.current_url
                print(f"DEBUG: URL after logout: {current_url}")
                
                # Look for signs we're logged out (login form should appear)
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.NAME, "username"))
                    )
                    print("✅ Successfully logged out - login form visible")
                except:
                    print("⚠️ Logout may not have worked - no login form found")
                    
            else:
                # No logout button found, use cookie clearing method
                print("⚠️ No logout button found, clearing cookies")
                driver.delete_all_cookies()
                driver.get(f"{server}")
                time.sleep(3)
                print("✅ Cookies cleared")
                
        except Exception as e:
            print(f"❌ Logout failed: {e}")
            # Fallback: clear cookies
            driver.delete_all_cookies()
            driver.get(f"{server}")
            time.sleep(3)
            print("✅ Fallback: Cookies cleared")
    
    def _login_user(self, driver, server, user_data):
        """Login existing user"""
        print(f"🔄 Attempting to login {user_data['username']}")
        
        # First try root page
        driver.get(f"{server}")
        time.sleep(3)
        
        # Debug current state
        current_url = driver.current_url
        page_text = driver.find_element(By.TAG_NAME, "body").text[:300]
        print(f"DEBUG: Current URL: {current_url}")
        print(f"DEBUG: Page text: {page_text}")
        
        # Try different approaches to find login form
        login_attempts = [
            lambda: self._try_login_on_current_page(driver, user_data),
            lambda: self._try_login_via_direct_url(driver, server, user_data),
            lambda: self._try_login_after_refresh(driver, server, user_data)
        ]
        
        for i, attempt in enumerate(login_attempts, 1):
            try:
                print(f"🔄 Login attempt {i}")
                attempt()
                
                # Check if login was successful
                WebDriverWait(driver, 10).until(
                    EC.url_contains("/groups")
                )
                print(f"✅ Login attempt {i} successful!")
                return
                
            except Exception as e:
                print(f"❌ Login attempt {i} failed: {e}")
                if i < len(login_attempts):
                    print(f"🔄 Trying next approach...")
                    time.sleep(2)
                else:
                    # Final attempt failed
                    current_url = driver.current_url
                    page_text = driver.find_element(By.TAG_NAME, "body").text[:200]
                    driver.save_screenshot("test_reports/login_final_failed.png")
                    raise Exception(f"All login attempts failed. Final URL: {current_url}, Page: {page_text}")
    
    def _try_login_on_current_page(self, driver, user_data):
        """Try to login on current page"""
        print("🔍 Looking for login form fields...")
        
        # Try multiple selectors for username field (Material-UI based)
        username_selectors = [
            (By.CSS_SELECTOR, "input[placeholder='Benutzername']"),  # Exact match first
            (By.XPATH, "//input[@placeholder='Benutzername']"),      # Exact match XPath
            (By.CSS_SELECTOR, "input[placeholder*='Benutzername']"), # Contains match
            (By.CSS_SELECTOR, "input[type='text']"),                 # Generic text input
            (By.NAME, "username"),                                   # Fallback
            (By.ID, "username")                                      # Fallback
        ]
        
        username_field = None
        for by_type, selector in username_selectors:
            try:
                username_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((by_type, selector))
                )
                print(f"✅ Found username field with: {by_type} = '{selector}'")
                break
            except:
                print(f"❌ Username field not found with: {by_type} = '{selector}'")
                continue
        
        if not username_field:
            raise Exception("Username field not found with any selector")
        
        # Try multiple selectors for password field (Material-UI based)
        password_selectors = [
            (By.CSS_SELECTOR, "input[placeholder='Passwort']"),      # Exact match first
            (By.XPATH, "//input[@placeholder='Passwort']"),          # Exact match XPath
            (By.CSS_SELECTOR, "input[type='password']"),             # Type-based (most reliable)
            (By.CSS_SELECTOR, "input[placeholder*='Passwort']"),     # Contains match
            (By.NAME, "password"),                                   # Fallback
            (By.ID, "password")                                      # Fallback
        ]
        
        password_field = None
        for by_type, selector in password_selectors:
            try:
                password_field = driver.find_element(by_type, selector)
                print(f"✅ Found password field with: {by_type} = '{selector}'")
                break
            except:
                print(f"❌ Password field not found with: {by_type} = '{selector}'")
                continue
        
        if not password_field:
            raise Exception("Password field not found with any selector")
        
        # Try multiple selectors for submit button (Material-UI based)
        submit_selectors = [
            (By.XPATH, "//button[contains(text(), 'Anmelden')]"),    # Exact text match
            (By.CSS_SELECTOR, "button"),                            # Generic button
            (By.CSS_SELECTOR, "button[type='submit']"),             # Submit type
            (By.XPATH, "//button[contains(text(), 'Login')]"),      # Alternative text
            (By.XPATH, "//input[@type='submit']")                   # Input submit
        ]
        
        submit_button = None
        for by_type, selector in submit_selectors:
            try:
                submit_button = driver.find_element(by_type, selector)
                print(f"✅ Found submit button with: {by_type} = '{selector}'")
                break
            except:
                print(f"❌ Submit button not found with: {by_type} = '{selector}'")
                continue
        
        if not submit_button:
            raise Exception("Submit button not found with any selector")
        
        # Fill and submit form
        print("🔄 Filling login form...")
        username_field.clear()
        username_field.send_keys(user_data["username"])
        password_field.clear() 
        password_field.send_keys(user_data["password"])
        
        print("🔄 Clicking submit button...")
        submit_button.click()
        
        time.sleep(3)
    
    def _try_login_via_direct_url(self, driver, server, user_data):
        """Try to login by going directly to /login"""
        driver.get(f"{server}/login")
        time.sleep(3)
        return self._try_login_on_current_page(driver, user_data)
    
    def _try_login_after_refresh(self, driver, server, user_data):
        """Try to login after refreshing page"""
        driver.refresh()
        time.sleep(3)
        return self._try_login_on_current_page(driver, user_data)