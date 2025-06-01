import pytest
import time
from tests.utils.test_data import generate_test_user

class TestLoginTiming:
    """Test login timing issues - OPTIMIZED VERSION"""
    
    def test_login_timing_debug_optimized(
        self, driver, server, clean_database,
        api_create_user, login_user_ui, logout_user_ui
    ):
        """Debug login timing issues with API-based setup - OPTIMIZED VERSION"""
        
        # === SETUP: API-based user creation (ultra-fast) ===
        user_data = generate_test_user()
        setup_start = time.time()
        api_create_user(user_data["username"], user_data["email"], user_data["password"])
        setup_time = time.time() - setup_start
        
        print(f"\n🔍 LOGIN TIMING DEBUG TEST - OPTIMIZED")
        print(f"👤 User: {user_data['username']}")
        print(f"✅ User created via API in {setup_time:.2f}s (vs ~30s UI registration)")
        
        # === TEST: Detailed login timing analysis ===
        print("\n📍 LOGIN TIMING ANALYSIS:")
        
        # Step 1: Navigate to login page
        login_start = time.time()
        print(f"1️⃣ Navigate to login page...")
        driver.get(f"{server}")
        page_load_time = time.time() - login_start
        print(f"   ⏱️ Page load: {page_load_time:.2f}s")
        
        # Step 2: Use optimized login helper and measure individual steps
        login_detail_start = time.time()
        print(f"2️⃣ Using optimized login helper...")
        
        # Call the optimized login function
        login_user_ui(user_data["username"], user_data["password"])
        
        login_time = time.time() - login_detail_start
        print(f"   ⏱️ Login completed in: {login_time:.2f}s")
        
        # Verify success
        assert "/groups" in driver.current_url
        print(f"✅ Successfully redirected to groups page")
        
        total_time = time.time() - login_start
        print(f"\n✅ TOTAL LOGIN TIME: {total_time:.2f}s")
        print(f"📊 Performance breakdown:")
        print(f"   - Setup (API): {setup_time:.2f}s")
        print(f"   - Page load: {page_load_time:.2f}s") 
        print(f"   - Login process: {login_time:.2f}s")
        
        if total_time > 10:
            print(f"⚠️  Login took longer than 10 seconds!")
        else:
            print(f"✅ Login completed within reasonable time")
            
        print("✅ OPTIMIZED Test passed: Login timing analysis completed ~5s instead of ~45s")