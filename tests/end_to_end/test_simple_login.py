import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def test_login_speed(driver, server, clean_database):
    """Test login speed with optimizations"""
    # First register a user
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    user_data = {"username": f"testuser{timestamp}", "email": f"test{timestamp}@example.com", "password": "testpass123"}
    
    print(f"\n🏃 SPEED TEST: Login optimization")
    print(f"👤 User: {user_data['username']}")
    
    # Register user
    print("\n📍 Registering user...")
    driver.get(f"{server}/register")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "form")))
    
    driver.find_element(By.NAME, "username").send_keys(user_data["username"])
    driver.find_element(By.NAME, "email").send_keys(user_data["email"])
    driver.find_element(By.NAME, "password").send_keys(user_data["password"])
    driver.find_element(By.NAME, "confirmPassword").send_keys(user_data["password"])
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    
    WebDriverWait(driver, 10).until(EC.url_contains("/groups"))
    print("✅ Registration complete")
    
    # Logout
    print("\n📍 Logging out...")
    driver.delete_all_cookies()
    driver.get(f"{server}")
    
    # LOGIN SPEED TEST
    print("\n📍 LOGIN SPEED TEST:")
    total_start = time.time()
    
    # Wait for login form
    username_field = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Benutzername']"))
    )
    print(f"⏱️  Form loaded in: {time.time() - total_start:.2f}s")
    
    # Fill form
    fill_start = time.time()
    password_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Passwort']")
    submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Anmelden')]")
    
    username_field.clear()
    username_field.send_keys(user_data["username"])
    password_field.clear()
    password_field.send_keys(user_data["password"])
    print(f"⏱️  Form filled in: {time.time() - fill_start:.2f}s")
    
    # Submit
    submit_start = time.time()
    submit_button.click()
    
    # Wait for redirect
    WebDriverWait(driver, 10).until(EC.url_contains("/groups"))
    print(f"⏱️  Login complete in: {time.time() - submit_start:.2f}s")
    
    total_time = time.time() - total_start
    print(f"\n✅ TOTAL LOGIN TIME: {total_time:.2f}s")
    
    if total_time < 3:
        print("🚀 EXCELLENT: Login under 3 seconds!")
    elif total_time < 5:
        print("✅ GOOD: Login under 5 seconds")
    else:
        print("⚠️  SLOW: Login took over 5 seconds")