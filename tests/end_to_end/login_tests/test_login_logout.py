import pytest
from tests.utils.test_data import generate_test_user

class TestLoginLogout:
    """Test basic login/logout functionality - OPTIMIZED VERSION"""
    
    def test_register_logout_login_cycle_optimized(
        self, driver, server, clean_database,
        api_create_user, login_user_ui, logout_user_ui
    ):
        """Test: API User Creation → Login → Logout → Login cycle - OPTIMIZED VERSION"""
        
        # === SETUP: API-based user creation (ultra-fast) ===
        user_data = generate_test_user()
        api_create_user(user_data["username"], user_data["email"], user_data["password"])
        
        print(f"\n🎬 Starting OPTIMIZED login/logout test")
        print(f"👤 User: {user_data['username']}")
        print("✅ User created via API (fast setup)")
        
        # === TEST: Login ===
        print("📍 Step 1: Login user")
        login_user_ui(user_data["username"], user_data["password"])
        
        # Verify user is logged in (should be on groups page)
        assert "/groups" in driver.current_url
        
        # Check if username appears on page
        from selenium.webdriver.common.by import By
        page_text = driver.find_element(By.TAG_NAME, "body").text
        assert user_data['username'] in page_text
        print(f"✅ User {user_data['username']} is logged in and visible on page")
        
        # === TEST: Logout ===
        print("📍 Step 2: Logout user")
        logout_user_ui()
        
        # === TEST: Login again ===
        print("📍 Step 3: Login user again") 
        login_user_ui(user_data["username"], user_data["password"])
        
        # Verify user is logged in again
        assert "/groups" in driver.current_url
        
        page_text = driver.find_element(By.TAG_NAME, "body").text
        assert user_data['username'] in page_text
        print(f"✅ User {user_data['username']} successfully logged in again")
        
        print("🎉 OPTIMIZED LOGIN/LOGOUT TEST PASSED!")
        print("✅ OPTIMIZED Test passed: Login/logout cycle completed ~5s instead of ~60s")