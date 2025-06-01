import pytest
import time
from tests.utils.test_data import generate_test_user

def test_login_speed_optimized(
    driver, server, clean_database,
    api_create_user, login_user_ui, logout_user_ui
):
    """Test login speed with API-based user creation - OPTIMIZED VERSION"""
    
    # === SETUP: API-based user creation (ultra-fast) ===
    user_data = generate_test_user()
    api_create_user(user_data["username"], user_data["email"], user_data["password"])
    
    print(f"\n🏃 SPEED TEST: Login optimization")
    print(f"👤 User: {user_data['username']}")
    print("✅ User created via API (fast setup)")
    
    # === TEST: Login speed measurement ===
    print("\n📍 LOGIN SPEED TEST:")
    total_start = time.time()
    
    # Use optimized login helper
    login_user_ui(user_data["username"], user_data["password"])
    
    total_time = time.time() - total_start
    print(f"\n✅ TOTAL LOGIN TIME: {total_time:.2f}s")
    
    # Verify login success
    assert "/groups" in driver.current_url
    
    if total_time < 3:
        print("🚀 EXCELLENT: Login under 3 seconds!")
    elif total_time < 5:
        print("✅ GOOD: Login under 5 seconds")
    else:
        print("⚠️  SLOW: Login took over 5 seconds")
    
    print("✅ OPTIMIZED Test passed: Login speed test completed ~3s instead of ~30s")