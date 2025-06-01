import pytest
import subprocess
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sqlite3
import os
import bcrypt
from datetime import datetime

@pytest.fixture(scope="session")
def test_database():
    """Create a temporary test database"""
    test_db_path = "test_teamquiz.db"
    
    # Clean up any existing test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    yield test_db_path
    
    # Always cleanup test database after session
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"✅ Test database {test_db_path} cleaned up")

@pytest.fixture(scope="session")
def server(test_database):
    """Start single FastAPI server that serves both frontend and backend"""
    # Set environment variable for test database
    os.environ["TEST_DATABASE"] = test_database
    
    # Build frontend first
    build_process = subprocess.Popen(
        ["npm", "run", "build"],
        cwd="frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    build_process.wait()
    
    if build_process.returncode != 0:
        raise Exception("Frontend build failed")
    
    # Start the server with venv activated
    server_process = subprocess.Popen(
        ["bash", "-c", "source ../venv/bin/activate && uvicorn app:app --reload --port 8000"],
        cwd="backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    max_retries = 30
    for _ in range(max_retries):
        try:
            response = requests.get("http://localhost:8000")
            if response.status_code in [200, 404]:  # 404 is fine, means server is running
                break
        except requests.ConnectionError:
            time.sleep(1)
    else:
        server_process.terminate()
        raise Exception("Server failed to start")
    
    yield "http://localhost:8000"
    
    # Cleanup
    server_process.terminate()
    server_process.wait()
    print("🔴 Test server stopped")

@pytest.fixture
def driver():
    """Create WebDriver instance - Safari only, headless mode"""
    driver = None
    
    # Only Safari, no fallbacks
    try:
        # Safari with headless-like configuration
        safari_options = webdriver.SafariOptions()
        # Note: Safari doesn't support true headless mode, but we can minimize window interaction
        driver = webdriver.Safari(options=safari_options)
        driver.implicitly_wait(10)
        # Don't maximize window to reduce visual impact
        print("✅ Using Safari driver (headless-mode)")
    except Exception as safari_error:
        pytest.skip(f"Safari driver required but unavailable: {safari_error}")
    
    yield driver
    
    if driver:
        driver.quit()

@pytest.fixture
def clean_database(test_database):
    """Clean the test database before each test"""
    if os.path.exists(test_database):
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Clear all tables
        for table in tables:
            if table[0] != 'sqlite_sequence':  # Don't delete SQLite's internal table
                cursor.execute(f"DELETE FROM {table[0]}")
        
        conn.commit()
        conn.close()

@pytest.fixture
def wait_helper():
    """Helper for waiting for elements"""
    def wait_for_element(driver, locator, timeout=10):
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
    
    def wait_for_clickable(driver, locator, timeout=10):
        return WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
    
    def wait_for_text(driver, locator, text, timeout=10):
        return WebDriverWait(driver, timeout).until(
            EC.text_to_be_present_in_element(locator, text)
        )
    
    return {
        "element": wait_for_element,
        "clickable": wait_for_clickable,
        "text": wait_for_text
    }

@pytest.fixture
def api_create_user(server):
    """Create user via API endpoints - uses test database automatically"""
    def _create_user(username, email, password):
        import requests
        
        response = requests.post(f"{server}/register", json={
            "username": username,
            "email": email,
            "password": password,
            "confirmPassword": password
        })
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"User creation failed: {response.status_code} - {response.text}")
    
    return _create_user

@pytest.fixture
def api_create_group(server):
    """Create group via API endpoints - uses test database automatically"""
    def _create_group(group_name, auth_data=None):
        import requests
        
        headers = {}
        cookies = None
        if auth_data:
            headers.update({"Authorization": auth_data["Authorization"]})
            cookies = auth_data["cookies"]
        
        response = requests.post(f"{server}/gruppe-erstellen", 
            json={"gruppen_name": group_name},
            headers=headers,
            cookies=cookies
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Group creation failed: {response.status_code} - {response.text}")
    
    return _create_group

@pytest.fixture  
def api_create_subject(server):
    """Create subject via API endpoints - uses test database automatically"""
    def _create_subject(subject_name, group_name, auth_data=None):
        import requests
        
        headers = {}
        cookies = None
        if auth_data:
            headers.update({"Authorization": auth_data["Authorization"]})
            cookies = auth_data["cookies"]
        
        response = requests.post(f"{server}/fach-erstellen",
            json={"fach_name": subject_name, "gruppen_name": group_name},
            headers=headers,
            cookies=cookies
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Subject creation failed: {response.status_code} - {response.text}")
    
    return _create_subject

@pytest.fixture
def api_login(server):
    """Login via API and return auth token"""
    def _login(username, password):
        import requests
        
        response = requests.post(f"{server}/login", data={
            "username": username,
            "password": password
        })
        
        if response.status_code == 200:
            token_data = response.json()
            return {
                "Authorization": f"Bearer {token_data['access_token']}",
                "cookies": response.cookies
            }
        else:
            raise Exception(f"Login failed: {response.status_code} - {response.text}")
    
    return _login

@pytest.fixture
def api_update_flashcard(server):
    """Update flashcard via API"""
    def _update_flashcard(flashcard_id, frage, antworten, auth_data):
        import requests
        
        headers = {}
        cookies = None
        if auth_data:
            headers.update({"Authorization": auth_data["Authorization"]})
            cookies = auth_data["cookies"]
        
        response = requests.put(f"{server}/flashcard/update",
            json={
                "flashcard_id": flashcard_id,
                "frage": frage, 
                "antworten": antworten
            },
            headers=headers,
            cookies=cookies
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Flashcard update failed: {response.status_code} - {response.text}")
    
    return _update_flashcard

@pytest.fixture  
def api_delete_flashcard(server):
    """Delete flashcard via API"""
    def _delete_flashcard(flashcard_id, auth_data):
        import requests
        
        headers = {}
        cookies = None
        if auth_data:
            headers.update({"Authorization": auth_data["Authorization"]})
            cookies = auth_data["cookies"]
        
        response = requests.delete(f"{server}/flashcard/delete",
            json={"flashcard_id": flashcard_id},
            headers=headers,
            cookies=cookies
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Flashcard deletion failed: {response.status_code} - {response.text}")
    
    return _delete_flashcard

@pytest.fixture
def login_user_ui(driver, server):
    """Login user via UI - robust implementation copied from working tests"""
    def _login(username, password):
        print(f"🔄 Attempting to login {username}")
        
        # First try root page
        driver.get(f"{server}")
        time.sleep(1)
        
        # Try multiple selectors for username field (Material-UI Joy based)
        username_selectors = [
            (By.CSS_SELECTOR, "input[placeholder='Benutzername']"),  # Direct input placeholder
            (By.XPATH, "//input[@placeholder='Benutzername']"),      # XPath for placeholder
            (By.CSS_SELECTOR, "input[type='text']"),                 # Any text input
            (By.CSS_SELECTOR, ".MuiInput-input"),                    # Material-UI Joy input class
            (By.CSS_SELECTOR, "input"),                              # Any input as last resort
        ]
        
        username_field = None
        for by_type, selector in username_selectors:
            try:
                username_field = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((by_type, selector))
                )
                print(f"✅ Found username field with: {by_type} = '{selector}'")
                break
            except:
                continue
        
        if not username_field:
            raise Exception("Username field not found with any selector")
        
        # Try multiple selectors for password field (Material-UI Joy based)
        password_selectors = [
            (By.CSS_SELECTOR, "input[placeholder='Passwort']"),      # Direct placeholder match
            (By.XPATH, "//input[@placeholder='Passwort']"),          # XPath for placeholder
            (By.CSS_SELECTOR, "input[type='password']"),             # Type-based (most reliable)
            (By.CSS_SELECTOR, ".MuiInput-input[type='password']"),   # Material-UI Joy password class
        ]
        
        password_field = None
        for by_type, selector in password_selectors:
            try:
                password_field = driver.find_element(by_type, selector)
                print(f"✅ Found password field with: {by_type} = '{selector}'")
                break
            except:
                continue
        
        if not password_field:
            raise Exception("Password field not found with any selector")
        
        # Try multiple selectors for submit button (Material-UI Joy based)
        submit_selectors = [
            (By.XPATH, "//button[contains(text(), 'Anmelden')]"),    # Exact text match
            (By.CSS_SELECTOR, ".MuiButton-root"),                   # Material-UI Joy button class
            (By.CSS_SELECTOR, "button"),                            # Generic button
            (By.XPATH, "//button[contains(@class, 'MuiButton')]"),  # Any MUI button
        ]
        
        submit_button = None
        for by_type, selector in submit_selectors:
            try:
                submit_button = driver.find_element(by_type, selector)
                print(f"✅ Found submit button with: {by_type} = '{selector}'")
                break
            except:
                continue
        
        if not submit_button:
            raise Exception("Submit button not found with any selector")
        
        # Fill and submit form
        print("🔄 Filling login form...")
        username_field.clear()
        username_field.send_keys(username)
        password_field.clear() 
        password_field.send_keys(password)
        
        print("🔄 Clicking submit button...")
        submit_button.click()
        
        # Wait for groups page
        WebDriverWait(driver, 3).until(
            EC.url_contains("/groups")
        )
        print(f"✅ Login successful for {username}")
    
    return _login

@pytest.fixture
def logout_user_ui(driver):
    """Logout user via cookie deletion - fastest method"""
    def _logout():
        driver.delete_all_cookies()
        driver.refresh()
    
    return _logout

@pytest.fixture
def navigate_to_group(driver, server):
    """Navigate to specific group page"""
    def _navigate(group_name):
        driver.get(f"{server}/groups/{group_name}")
        
        # Wait for group page to load - try multiple selectors 
        try:
            # Wait for group page specific content
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".mittelPage"))
            )
        except:
            try:
                # Fallback to group title
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                )
            except:
                # Last fallback - any Material-UI card
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".MuiCard-root"))
                )
    
    return _navigate