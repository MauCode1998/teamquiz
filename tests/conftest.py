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
    """Create WebDriver instance"""
    driver = None
    
    # Try Safari first
    try:
        driver = webdriver.Safari()
        driver.implicitly_wait(10)
        driver.maximize_window()
        print("✅ Using Safari driver")
    except Exception as safari_error:
        # Fallback to Chrome
        try:
            from selenium.webdriver.chrome.options import Options
            chrome_options = Options()
            # chrome_options.add_argument("--headless")  # Uncomment for headless mode
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            driver.maximize_window()
            print("✅ Using Chrome driver (Safari unavailable)")
        except Exception as chrome_error:
            pytest.skip(f"Could not initialize any browser driver. Safari: {safari_error}. Chrome: {chrome_error}")
    
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