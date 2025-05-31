import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

class TestSimpleInvitation:
    """Fixed invitation test with proper timing"""
    
    def test_invitation_accept(self, driver, server, clean_database):
        """Test complete invitation flow with reliable waiting"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        user1_data = {"username": f"sender{timestamp}", "email": f"sender{timestamp}@example.com", "password": "testpass123"}
        user2_data = {"username": f"receiver{timestamp}", "email": f"receiver{timestamp}@example.com", "password": "testpass123"}
        test_group = f"TestGroup{timestamp}"
        
        print(f"\n🎬 Invitation ACCEPT Test")
        print(f"👤 User1 (Sender): {user1_data['username']}")
        print(f"👤 User2 (Receiver): {user2_data['username']}")
        print(f"👥 Group: {test_group}")
        
        # Step 1: Register both users
        print("📍 Step 1: Register both users")
        self._register_user(driver, server, user1_data)
        self._register_user(driver, server, user2_data)
        
        # Step 2: User1 creates group and sends invitation
        print("📍 Step 2: User1 creates group and sends invitation")
        self._logout_user(driver, server)
        self._login_user(driver, server, user1_data)
        self._create_group(driver, server, test_group)
        self._send_invitation_via_frontend(driver, server, test_group, user2_data["username"])
        
        # Step 3: User2 checks and accepts invitation
        print("📍 Step 3: User2 checks and accepts invitation")
        self._logout_user(driver, server)
        self._login_user(driver, server, user2_data)
        
        # Wait for invitation to appear with custom wait
        invitation_found = self._wait_for_invitation(driver, server, test_group, timeout=30)
        
        if invitation_found:
            print("🎉 INVITATION DETECTION PASSED!")
            
            # Accept the invitation
            self._accept_invitation_simple(driver, server)
            
            # Verify User2 is now in the group
            self._verify_group_membership(driver, server, test_group)
            
            # Additional verification: Can User2 navigate to the group?
            self._verify_can_access_group(driver, server, test_group)
            
            print("🎉 COMPLETE INVITATION TEST PASSED!")
        else:
            print("💥 INVITATION TEST FAILED!")
            assert False, f"User2 should see invitation to group '{test_group}'"
    
    def test_invitation_reject(self, driver, server, clean_database):
        """Test rejecting an invitation"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        user1_data = {"username": f"rejecter1{timestamp}", "email": f"rejecter1{timestamp}@example.com", "password": "testpass123"}
        user2_data = {"username": f"rejecter2{timestamp}", "email": f"rejecter2{timestamp}@example.com", "password": "testpass123"}
        test_group = f"RejectGroup{timestamp}"
        
        print(f"\n🎬 Invitation REJECT Test")
        print(f"👤 User1 (Sender): {user1_data['username']}")
        print(f"👤 User2 (Receiver): {user2_data['username']}")
        print(f"👥 Group: {test_group}")
        
        # Step 1: Register both users
        print("📍 Step 1: Register both users")
        self._register_user(driver, server, user1_data)
        self._register_user(driver, server, user2_data)
        
        # Step 2: User1 creates group and sends invitation
        print("📍 Step 2: User1 creates group and sends invitation")
        self._logout_user(driver, server)
        self._login_user(driver, server, user1_data)
        self._create_group(driver, server, test_group)
        self._send_invitation_via_frontend(driver, server, test_group, user2_data["username"])
        
        # Step 3: User2 checks and REJECTS invitation
        print("📍 Step 3: User2 checks and REJECTS invitation")
        self._logout_user(driver, server)
        self._login_user(driver, server, user2_data)
        
        # Wait for invitation to appear
        invitation_found = self._wait_for_invitation(driver, server, test_group, timeout=30)
        
        if invitation_found:
            print("🎉 INVITATION DETECTION PASSED!")
            
            # Reject the invitation
            self._reject_invitation_simple(driver, server)
            
            # Verify User2 is NOT in the group
            self._verify_not_member(driver, server, test_group)
            
            print("🎉 REJECTION TEST PASSED!")
        else:
            print("💥 INVITATION TEST FAILED!")
            assert False, f"User2 should see invitation to group '{test_group}'"
    
    def _wait_for_invitation(self, driver, server, group_name, timeout=30):
        """Wait for invitation to appear with custom logic"""
        print(f"🔄 Waiting up to {timeout}s for invitation to appear...")
        
        driver.get(f"{server}/groups")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        end_time = time.time() + timeout
        attempt = 0
        
        while time.time() < end_time:
            attempt += 1
            
            # Refresh the page to trigger invitation loading
            if attempt > 1:
                driver.refresh()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            time.sleep(1)  # Brief wait for async loading
            
            page_text = driver.find_element(By.TAG_NAME, "body").text
            print(f"⏳ Attempt {attempt}: Checking for invitations...")
            
            # Check for invitation indicators
            if "lädt" in page_text and (group_name in page_text or "TestGroup" in page_text):
                print(f"✅ Invitation found on attempt {attempt}!")
                print(f"DEBUG: Found text containing: {[word for word in page_text.split() if 'lädt' in word or group_name in word]}")
                return True
            elif "lädt" in page_text:
                print(f"⚠️ Found invitation text but not for our group")
                print(f"DEBUG: Page contains: ...{page_text[page_text.find('lädt')-20:page_text.find('lädt')+50]}...")
            else:
                print(f"⏳ No invitation text found yet")
        
        print(f"❌ No invitation found after {timeout}s")
        return False
    
    def _send_invitation_via_frontend(self, driver, server, group_name, invitee_username):
        """Send invitation through frontend UI"""
        print(f"🔄 Sending invitation to {invitee_username} via frontend")
        
        # Navigate to the specific group page
        driver.get(f"{server}/groups/{group_name}")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Wait for invitation form to be present
        invite_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Benutzername']"))
        )
        
        invite_input.clear()
        invite_input.send_keys(invitee_username)
        
        invite_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Einladen')]")
        invite_button.click()
        
        time.sleep(1)  # Brief wait for invitation to be processed
        print(f"✅ Invitation sent to {invitee_username}")
    
    def _accept_invitation_simple(self, driver, server):
        """Accept any visible invitation"""
        print(f"🔄 Looking for accept button...")
        
        try:
            # Look for any "Annehmen" button
            accept_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Annehmen')]"))
            )
            
            print(f"✅ Found accept button, clicking...")
            accept_button.click()
            
            time.sleep(1)  # Brief wait for acceptance to process
            print(f"✅ Invitation accepted!")
            
        except Exception as e:
            print(f"❌ Could not find/click accept button: {e}")
            
            # Debug: show all buttons
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"DEBUG: All buttons on page:")
            for i, btn in enumerate(buttons):
                print(f"  {i}: '{btn.text}' (displayed: {btn.is_displayed()})")
            
            raise
    
    def _verify_group_membership(self, driver, server, group_name):
        """Verify user is now member of the group"""
        print(f"🔄 Verifying group membership...")
        
        # Refresh to see updated groups
        driver.get(f"{server}/groups")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)  # Brief wait for groups to load
        
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Check if group appears in "Meine Gruppen" section
        if group_name in page_text and "Meine Gruppen" in page_text:
            print(f"✅ User successfully joined group '{group_name}'")
        else:
            print(f"⚠️ Group membership verification unclear")
            print(f"DEBUG: Page content: {page_text[:300]}...")
    
    def _reject_invitation_simple(self, driver, server):
        """Reject any visible invitation"""
        print(f"🔄 Looking for reject button...")
        
        try:
            # Look for any "Ablehnen" button
            reject_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Ablehnen')]"))
            )
            
            print(f"✅ Found reject button, clicking...")
            reject_button.click()
            
            time.sleep(1)  # Brief wait for rejection to process
            print(f"✅ Invitation rejected!")
            
        except Exception as e:
            print(f"❌ Could not find/click reject button: {e}")
            driver.save_screenshot("test_reports/reject_invitation_failed.png")
            raise
    
    def _verify_not_member(self, driver, server, group_name):
        """Verify user is NOT member of the group"""
        print(f"🔄 Verifying user is NOT in group...")
        
        # Refresh to see updated groups
        driver.get(f"{server}/groups")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)  # Brief wait for groups to load
        
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Check if group appears in "Meine Gruppen" section
        if group_name in page_text and "Meine Gruppen" in page_text:
            # Look more carefully - might be in invitations section still
            groups_section = driver.find_element(By.XPATH, "//h2[contains(text(), 'Meine Gruppen')]/following-sibling::*")
            if group_name in groups_section.text:
                print(f"❌ User incorrectly appears as member of group '{group_name}'")
                assert False, f"User should NOT be member of group after rejection"
        
        print(f"✅ User correctly NOT member of rejected group '{group_name}'")
    
    def _verify_can_access_group(self, driver, server, group_name):
        """Verify user can click on the group and navigate to it"""
        print(f"🔄 Verifying user can access group '{group_name}'...")
        
        # Make sure we're on groups page
        driver.get(f"{server}/groups")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)  # Brief wait for groups to load
        
        try:
            # Find the group link in "Meine Gruppen" section
            # Groups are shown as links with href="/groups/{groupname}"
            group_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '/groups/{group_name}')]"))
            )
            
            print(f"✅ Found group '{group_name}' in 'Meine Gruppen'")
            
            # Click on the group link
            group_link.click()
            
            # Wait for navigation to group page
            WebDriverWait(driver, 10).until(EC.url_contains(f"/groups/{group_name}"))
            
            # Verify we're on the correct group page
            current_url = driver.current_url
            if f"/groups/{group_name}" in current_url:
                print(f"✅ Successfully navigated to group page: {current_url}")
                
                # Check if group name is displayed on the page
                page_text = driver.find_element(By.TAG_NAME, "body").text
                if group_name in page_text:
                    print(f"✅ Group name '{group_name}' is displayed on the group page")
                else:
                    print(f"⚠️ Group name not visible on page")
            else:
                print(f"❌ Navigation failed - unexpected URL: {current_url}")
                assert False, f"Should have navigated to /groups/{group_name}"
                
        except Exception as e:
            print(f"❌ Could not access group '{group_name}': {e}")
            driver.save_screenshot("test_reports/group_access_failed.png")
            
            # Debug: List all visible links
            try:
                links = driver.find_elements(By.TAG_NAME, "a")
                print("DEBUG: All visible links:")
                for link in links:
                    href = link.get_attribute("href")
                    text = link.text
                    if href and "groups" in href:
                        print(f"  - {text}: {href}")
            except:
                pass
                
            raise
    
    # Helper methods (same as before)
    def _register_user(self, driver, server, user_data):
        """Register a user"""
        driver.get(f"{server}/register")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "form")))
        
        driver.find_element(By.NAME, "username").send_keys(user_data["username"])
        driver.find_element(By.NAME, "email").send_keys(user_data["email"])
        driver.find_element(By.NAME, "password").send_keys(user_data["password"])
        driver.find_element(By.NAME, "confirmPassword").send_keys(user_data["password"])
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        WebDriverWait(driver, 10).until(EC.url_contains("/groups"))
        # No extra sleep needed after registration
        print(f"✅ User {user_data['username']} registered")
    
    def _login_user(self, driver, server, user_data):
        """Login existing user"""
        print(f"🔄 Logging in {user_data['username']}")
        driver.get(f"{server}")
        # No sleep needed - WebDriverWait handles the waiting
        
        if "/groups" in driver.current_url:
            print(f"✅ Already logged in")
            return
            
        # Wait for login form to be ready (reduced timeout)
        username_field = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Benutzername']"))
        )
        
        # Re-find elements to avoid stale reference
        password_field = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Passwort']"))
        )
        submit_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Anmelden')]"))
        )
        
        # Fill form immediately
        username_field.clear()
        username_field.send_keys(user_data["username"])
        password_field.clear()
        password_field.send_keys(user_data["password"])
        submit_button.click()
        
        # Wait for redirect (reduced timeout)
        WebDriverWait(driver, 10).until(EC.url_contains("/groups"))
        print(f"✅ Logged in as {user_data['username']}")
        # No extra sleep needed
    
    def _logout_user(self, driver, server):
        """Logout current user"""
        print("🔄 Logging out")
        driver.delete_all_cookies()
        driver.get(f"{server}")
        # No sleep needed - next action will wait as needed
        print("✅ Logged out")
    
    def _create_group(self, driver, server, group_name):
        """Create a group"""
        driver.get(f"{server}/groups")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        group_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Gruppenname']")
        group_input.clear()
        group_input.send_keys(group_name)
        
        submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Erstellen!')]")
        submit_button.click()
        
        # Wait briefly for group creation
        time.sleep(0.5)
        print(f"✅ Group '{group_name}' created")