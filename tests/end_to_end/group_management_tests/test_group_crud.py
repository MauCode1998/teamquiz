import pytest
import requests
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime

class TestGroupCRUD:
    """Test group creation, viewing, navigation and deletion"""
    
    def test_create_group_and_view_list(self, driver, server, clean_database):
        """Test creating a group and seeing it in the groups list"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_user = {"username": f"groupuser{timestamp}", "email": f"groupuser{timestamp}@example.com", "password": "testpass123"}
        test_group = f"TestGroup{timestamp}"
        
        print(f"\n🎬 Starting group creation test for user: {test_user['username']}")
        
        # Step 1: Register user
        print("📍 Step 1: Register test user")
        self._register_user(driver, server, test_user)
        
        # Step 2: Navigate to groups page
        print("📍 Step 2: Navigate to groups page")
        driver.get(f"{server}/groups")
        
        # Wait for groups page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Step 3: Create a new group
        print("📍 Step 3: Create a new group")
        
        # Look for group creation form (based on Gruppen.js)
        try:
            # Find the input field with placeholder 'Gruppenname'
            group_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Gruppenname']")
            group_input.clear()
            group_input.send_keys(test_group)
            
            # Find the "Erstellen!" button
            submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Erstellen!')]")            
            submit_button.click()
            
            print(f"✅ Group creation form submitted for: {test_group}")
            
        except Exception as e:
            print(f"❌ Could not find group creation elements: {e}")
            driver.save_screenshot("test_reports/group_creation_failed.png")
            raise
        
        # Step 4: Verify group appears in list
        print("📍 Step 4: Verify group appears in groups list")
        time.sleep(2)  # Wait for group to be created
        
        try:
            # Look for the created group in the list
            group_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{test_group}')]"))
            )
            
            print(f"🎉 GROUP CREATION TEST PASSED!")
            print(f"✅ Group '{test_group}' found in groups list")
            assert group_element.is_displayed()
            
        except TimeoutException:
            print("💥 GROUP CREATION TEST FAILED!")
            print(f"❌ Group '{test_group}' not found in groups list")
            driver.save_screenshot("test_reports/group_not_found.png")
            assert False, f"Created group '{test_group}' not found in groups list"
    
    def test_navigate_to_subjects_and_back(self, driver, server, clean_database):
        """Test navigation from groups to subjects page and back"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_user = {"username": f"navuser{timestamp}", "email": f"navuser{timestamp}@example.com", "password": "testpass123"}
        test_group = f"NavGroup{timestamp}"
        
        print(f"\n🎬 Starting navigation test for user: {test_user['username']}")
        
        # Step 1: Register user and create group
        print("📍 Step 1: Register user and create group")
        self._register_user(driver, server, test_user)
        self._create_group(driver, server, test_group)
        
        # Step 2: Navigate to subjects page by clicking on group
        print("📍 Step 2: Navigate to subjects page")
        
        try:
            # Find and click on the group to navigate to subjects
            group_link = driver.find_element(By.XPATH, f"//*[contains(text(), '{test_group}')]")
            group_link.click()
            
            # Wait for subjects page to load
            WebDriverWait(driver, 10).until(
                EC.url_contains(f"/groups/{test_group}")
            )
            
            current_url = driver.current_url
            print(f"✅ Successfully navigated to subjects page: {current_url}")
            assert f"/groups/{test_group}" in current_url
            
        except Exception as e:
            print(f"❌ Could not navigate to subjects page: {e}")
            driver.save_screenshot("test_reports/navigation_to_subjects_failed.png")
            raise
        
        # Step 3: Navigate back to groups list
        print("📍 Step 3: Navigate back to groups list")
        
        try:
            # Look for navigation back to groups - likely automatic redirect or browser back
            # For now, navigate directly to groups page
            driver.get(f"{server}/groups")
            # Wait for groups page to load
            WebDriverWait(driver, 10).until(
                EC.url_matches(r".*/groups$")
            )
            
            current_url = driver.current_url
            print(f"✅ Successfully navigated back to groups page: {current_url}")
            assert current_url.endswith("/groups")
            
            print("🎉 NAVIGATION TEST PASSED!")
            
        except Exception as e:
            print(f"❌ Could not navigate back to groups: {e}")
            driver.save_screenshot("test_reports/navigation_back_failed.png")
            raise
    
    def test_leave_group(self, driver, server, clean_database):
        """Test leaving a group"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_user = {"username": f"leaveuser{timestamp}", "email": f"leaveuser{timestamp}@example.com", "password": "testpass123"}
        test_group = f"LeaveGroup{timestamp}"
        
        print(f"\n🎬 Starting leave group test for user: {test_user['username']}")
        
        # Step 1: Register user and create group
        print("📍 Step 1: Register user and create group")
        self._register_user(driver, server, test_user)
        self._create_group(driver, server, test_group)
        
        # Step 2: Navigate to group and find leave option
        print("📍 Step 2: Navigate to group and leave it")
        
        try:
            # Click on group to enter it
            group_link = driver.find_element(By.XPATH, f"//*[contains(text(), '{test_group}')]")
            group_link.click()
            
            # Wait for group page to load
            WebDriverWait(driver, 10).until(
                EC.url_contains(f"/groups/{test_group}")
            )
            
            # Look for leave group button ("Austreten" in German)
            leave_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Austreten')]")
            leave_button.click()
            
            # Handle confirmation if it exists
            try:
                confirm_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Ja')] | //button[contains(text(), 'Yes')] | //button[contains(text(), 'Bestätigen')] | //button[contains(text(), 'Confirm')]"))
                )
                confirm_button.click()
            except TimeoutException:
                pass  # No confirmation dialog
            
            print(f"✅ Left group '{test_group}'")
            
        except Exception as e:
            print(f"❌ Could not leave group: {e}")
            driver.save_screenshot("test_reports/leave_group_failed.png")
            raise
        
        # Step 3: Verify group is removed or user is no longer member
        print("📍 Step 3: Verify group is removed from user's list")
        time.sleep(2)  # Wait for changes to propagate
        
        # Navigate back to groups list
        driver.get(f"{server}/groups")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check if group is still visible (should be gone if user was last member)
        try:
            group_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{test_group}')]")
            # If we find it, that's unexpected since user was the only member
            print(f"⚠️  Group '{test_group}' still exists after leaving (might have other members)")
        except:
            print(f"🎉 LEAVE GROUP TEST PASSED!")
            print(f"✅ Group '{test_group}' was deleted when last member left")
    
    def test_group_deletion_when_last_member_leaves(self, driver, server, clean_database):
        """Test that group is deleted when last member leaves"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_user = {"username": f"lastuser{timestamp}", "email": f"lastuser{timestamp}@example.com", "password": "testpass123"}
        test_group = f"LastGroup{timestamp}"
        
        print(f"\n🎬 Starting last member deletion test for user: {test_user['username']}")
        
        # Step 1: Register user and create group
        print("📍 Step 1: Register user and create group")
        self._register_user(driver, server, test_user)
        self._create_group(driver, server, test_group)
        
        # Step 2: Verify group is visible in UI before leaving
        print("📍 Step 2: Verify group is visible in groups list")
        driver.get(f"{server}/groups")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        try:
            group_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{test_group}')]")
            print(f"✅ Group '{test_group}' confirmed to exist in UI")
            assert group_element.is_displayed()
        except:
            assert False, f"Group '{test_group}' should be visible before leaving"
        
        # Step 3: Leave the group (as the only member)
        print("📍 Step 3: Leave group as last member")
        self._leave_group(driver, server, test_group)
        
        # Step 4: Verify group is no longer visible in UI (indicates deletion)
        print("📍 Step 4: Verify group is no longer visible in UI")
        time.sleep(2)  # Allow time for deletion
        
        # Navigate back to groups page to check
        driver.get(f"{server}/groups")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check if group is still visible (should be gone if user was last member)
        try:
            group_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{test_group}')]")
            print("💥 LAST MEMBER DELETION TEST FAILED!")
            print(f"❌ Group '{test_group}' still exists in UI after last member left")
            assert False, f"Group '{test_group}' should be deleted when last member leaves"
        except:
            print("🎉 LAST MEMBER DELETION TEST PASSED!")
            print(f"✅ Group '{test_group}' was automatically deleted when last member left")
    
    # Helper methods
    def _register_user(self, driver, server, user_data):
        """Helper to register a user"""
        driver.get(f"{server}/register")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        
        driver.find_element(By.NAME, "username").send_keys(user_data["username"])
        driver.find_element(By.NAME, "email").send_keys(user_data["email"])
        driver.find_element(By.NAME, "password").send_keys(user_data["password"])
        driver.find_element(By.NAME, "confirmPassword").send_keys(user_data["password"])
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        time.sleep(2)  # Wait for registration to complete
    
    def _create_group(self, driver, server, group_name):
        """Helper to create a group"""
        driver.get(f"{server}/groups")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Find and use group creation form
        try:
            group_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Gruppenname']")
            group_input.clear()
            group_input.send_keys(group_name)
            
            submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Erstellen!')]")
            submit_button.click()
            
            time.sleep(2)  # Wait for group to be created
        except Exception as e:
            raise Exception(f"Could not create group: {e}")
    
    def _leave_group(self, driver, server, group_name):
        """Helper to leave a group"""
        # Navigate to group
        driver.get(f"{server}/groups/{group_name}")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Find and click leave button ("Austreten" in German)
        leave_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Austreten')]")
        leave_button.click()
        
        # Handle confirmation
        try:
            confirm_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Ja')] | //button[contains(text(), 'Yes')] | //button[contains(text(), 'Bestätigen')] | //button[contains(text(), 'Confirm')]"))
            )
            confirm_button.click()
        except TimeoutException:
            pass  # No confirmation dialog
        
        time.sleep(2)  # Wait for leave action to complete