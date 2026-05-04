"""
TaskFlow – Selenium Test Suite (20 Test Cases)
================================================
Requirements:
    pip install selenium pytest

Run:
    # Start the app first:  python app.py
    # Then in another terminal:
    pytest test_taskflow.py -v

For headless Chrome on Jenkins/EC2:
    Tests already use headless mode by default (see get_driver()).
"""

import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# ── Config ────────────────────────────────────────────────────────────────────

BASE_URL     = "http://127.0.0.1:5000"
TEST_USER    = "testuser_selenium"
TEST_EMAIL   = "selenium@taskflow.test"
TEST_PASS    = "TestPass@123"
WAIT_TIMEOUT = 10   # seconds


# ── Driver Factory ────────────────────────────────────────────────────────────

def get_driver():
    """Return a headless Chrome WebDriver."""
    options = Options()
    options.add_argument("--headless")          # Required for Jenkins/EC2
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--remote-debugging-port=9222")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    return driver


def wait_for(driver, by, value, timeout=WAIT_TIMEOUT):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def register_user(driver, username=TEST_USER, email=TEST_EMAIL, password=TEST_PASS):
    """Helper: register a user (ignores error if already exists)."""
    driver.get(f"{BASE_URL}/register")
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "email").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "confirm_password").send_keys(password)
    driver.find_element(By.ID, "register-btn").click()


def login_user(driver, username=TEST_USER, password=TEST_PASS):
    """Helper: log in with given credentials."""
    driver.get(f"{BASE_URL}/login")
    driver.find_element(By.ID, "username").clear()
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "login-btn").click()


# ═════════════════════════════════════════════════════════════════════════════
# TEST CASES
# ═════════════════════════════════════════════════════════════════════════════

class TestAuthentication:
    """TC-01 to TC-05: Registration & Login flows"""

    # ── TC-01 ─────────────────────────────────────────────────────────────────
    def test_01_register_page_loads(self):
        """TC-01: Register page loads and contains expected form fields."""
        driver = get_driver()
        try:
            driver.get(f"{BASE_URL}/register")
            assert "Register" in driver.title or "TaskFlow" in driver.title
            assert driver.find_element(By.ID, "username")
            assert driver.find_element(By.ID, "email")
            assert driver.find_element(By.ID, "password")
            assert driver.find_element(By.ID, "confirm_password")
            assert driver.find_element(By.ID, "register-btn")
        finally:
            driver.quit()

    # ── TC-02 ─────────────────────────────────────────────────────────────────
    def test_02_successful_registration(self):
        """TC-02: A new user can register successfully."""
        driver = get_driver()
        try:
            import random
            unique = f"user_{random.randint(10000, 99999)}"
            driver.get(f"{BASE_URL}/register")
            driver.find_element(By.ID, "username").send_keys(unique)
            driver.find_element(By.ID, "email").send_keys(f"{unique}@test.com")
            driver.find_element(By.ID, "password").send_keys("Pass@1234")
            driver.find_element(By.ID, "confirm_password").send_keys("Pass@1234")
            driver.find_element(By.ID, "register-btn").click()
            # Should redirect to login with a flash message
            wait_for(driver, By.ID, "login-form")
            assert "/login" in driver.current_url
        finally:
            driver.quit()

    # ── TC-03 ─────────────────────────────────────────────────────────────────
    def test_03_registration_password_mismatch(self):
        """TC-03: Registration fails when passwords do not match."""
        driver = get_driver()
        try:
            driver.get(f"{BASE_URL}/register")
            driver.find_element(By.ID, "username").send_keys("mismatch_user")
            driver.find_element(By.ID, "email").send_keys("mismatch@test.com")
            driver.find_element(By.ID, "password").send_keys("Pass@1234")
            driver.find_element(By.ID, "confirm_password").send_keys("Different@999")
            driver.find_element(By.ID, "register-btn").click()
            error = wait_for(driver, By.ID, "error-message")
            assert "Passwords do not match" in error.text
        finally:
            driver.quit()

    # ── TC-04 ─────────────────────────────────────────────────────────────────
    def test_04_successful_login(self):
        """TC-04: Registered user can log in and reaches the dashboard."""
        driver = get_driver()
        try:
            register_user(driver)         # ensure user exists
            login_user(driver)
            wait_for(driver, By.ID, "dashboard-heading")
            assert "/dashboard" in driver.current_url
        finally:
            driver.quit()

    # ── TC-05 ─────────────────────────────────────────────────────────────────
    def test_05_invalid_login_shows_error(self):
        """TC-05: Login with wrong password shows an error message."""
        driver = get_driver()
        try:
            driver.get(f"{BASE_URL}/login")
            driver.find_element(By.ID, "username").send_keys("nonexistent_xyz")
            driver.find_element(By.ID, "password").send_keys("WrongPass!")
            driver.find_element(By.ID, "login-btn").click()
            error = wait_for(driver, By.ID, "error-message")
            assert "Invalid" in error.text
        finally:
            driver.quit()


class TestDashboard:
    """TC-06 to TC-08: Dashboard UI and navigation."""

    # ── TC-06 ─────────────────────────────────────────────────────────────────
    def test_06_dashboard_stats_visible(self):
        """TC-06: Stats cards (total, pending, completed, high) are visible."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            wait_for(driver, By.ID, "stats-row")
            assert driver.find_element(By.ID, "stat-total")
            assert driver.find_element(By.ID, "stat-pending")
            assert driver.find_element(By.ID, "stat-completed")
            assert driver.find_element(By.ID, "stat-high")
        finally:
            driver.quit()

    # ── TC-07 ─────────────────────────────────────────────────────────────────
    def test_07_navbar_links_present(self):
        """TC-07: Navigation bar contains Dashboard, New Task, Search, Profile, Logout."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            nav_text = driver.find_element(By.TAG_NAME, "nav").text
            for label in ["Dashboard", "New Task", "Search", "Profile", "Logout"]:
                assert label in nav_text, f"'{label}' not found in nav"
        finally:
            driver.quit()

    # ── TC-08 ─────────────────────────────────────────────────────────────────
    def test_08_unauthenticated_redirect_to_login(self):
        """TC-08: Visiting /dashboard without login redirects to /login."""
        driver = get_driver()
        try:
            driver.get(f"{BASE_URL}/dashboard")
            time.sleep(1)
            assert "/login" in driver.current_url
        finally:
            driver.quit()


class TestTaskCRUD:
    """TC-09 to TC-15: Create, Read, Update, Delete tasks."""

    # ── TC-09 ─────────────────────────────────────────────────────────────────
    def test_09_add_task_page_loads(self):
        """TC-09: Add Task page loads with all required form fields."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            driver.get(f"{BASE_URL}/task/add")
            assert driver.find_element(By.ID, "title")
            assert driver.find_element(By.ID, "description")
            assert driver.find_element(By.ID, "priority")
            assert driver.find_element(By.ID, "due_date")
            assert driver.find_element(By.ID, "submit-task-btn")
        finally:
            driver.quit()

    # ── TC-10 ─────────────────────────────────────────────────────────────────
    def test_10_create_task_successfully(self):
        """TC-10: A new task can be created and appears on the dashboard."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            driver.get(f"{BASE_URL}/task/add")
            driver.find_element(By.ID, "title").send_keys("Selenium Test Task")
            driver.find_element(By.ID, "description").send_keys("Created by automated test")
            Select(driver.find_element(By.ID, "priority")).select_by_value("high")
            driver.find_element(By.ID, "submit-task-btn").click()
            wait_for(driver, By.ID, "task-table")
            assert "Selenium Test Task" in driver.page_source
        finally:
            driver.quit()

    # ── TC-11 ─────────────────────────────────────────────────────────────────
    def test_11_create_task_empty_title_shows_error(self):
        """TC-11: Submitting a task with an empty title shows a validation error."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            driver.get(f"{BASE_URL}/task/add")
            # Leave title blank; fill description only
            driver.find_element(By.ID, "description").send_keys("No title here")
            driver.find_element(By.ID, "submit-task-btn").click()
            # Browser HTML5 validation or server-side error
            time.sleep(0.5)
            # Either still on add page or error shown
            assert "/task/add" in driver.current_url or "required" in driver.page_source.lower()
        finally:
            driver.quit()

    # ── TC-12 ─────────────────────────────────────────────────────────────────
    def test_12_edit_task_updates_title(self):
        """TC-12: Editing a task changes its title on the dashboard."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            # Create task
            driver.get(f"{BASE_URL}/task/add")
            driver.find_element(By.ID, "title").send_keys("Original Title")
            driver.find_element(By.ID, "submit-task-btn").click()
            wait_for(driver, By.ID, "task-table")
            # Find edit button for first task
            edit_btn = driver.find_element(By.CSS_SELECTOR, "[id^='edit-btn-']")
            edit_btn.click()
            wait_for(driver, By.ID, "edit-task-form")
            title_field = driver.find_element(By.ID, "title")
            title_field.clear()
            title_field.send_keys("Updated Title")
            driver.find_element(By.ID, "update-task-btn").click()
            wait_for(driver, By.ID, "task-table")
            assert "Updated Title" in driver.page_source
        finally:
            driver.quit()

    # ── TC-13 ─────────────────────────────────────────────────────────────────
    def test_13_delete_task_removes_it(self):
        """TC-13: Deleting a task removes it from the task list."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            # Create a task to delete
            driver.get(f"{BASE_URL}/task/add")
            driver.find_element(By.ID, "title").send_keys("Task To Delete")
            driver.find_element(By.ID, "submit-task-btn").click()
            wait_for(driver, By.ID, "task-table")
            assert "Task To Delete" in driver.page_source
            # Accept confirm dialog automatically
            driver.execute_script(
                "window.confirm = function() { return true; };"
            )
            delete_btn = driver.find_element(By.CSS_SELECTOR, "[id^='delete-btn-']")
            delete_btn.click()
            time.sleep(1)
            assert "Task To Delete" not in driver.page_source
        finally:
            driver.quit()

    # ── TC-14 ─────────────────────────────────────────────────────────────────
    def test_14_mark_task_complete(self):
        """TC-14: Clicking 'Complete' changes a task's status to 'completed'."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            driver.get(f"{BASE_URL}/task/add")
            driver.find_element(By.ID, "title").send_keys("Task To Complete")
            driver.find_element(By.ID, "submit-task-btn").click()
            wait_for(driver, By.ID, "task-table")
            complete_btn = driver.find_element(By.CSS_SELECTOR, "[id^='complete-btn-']")
            complete_btn.click()
            time.sleep(0.7)
            assert "completed" in driver.page_source
        finally:
            driver.quit()

    # ── TC-15 ─────────────────────────────────────────────────────────────────
    def test_15_edit_task_priority_change(self):
        """TC-15: Changing priority in edit form is reflected on the dashboard."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            driver.get(f"{BASE_URL}/task/add")
            driver.find_element(By.ID, "title").send_keys("Priority Test Task")
            Select(driver.find_element(By.ID, "priority")).select_by_value("low")
            driver.find_element(By.ID, "submit-task-btn").click()
            wait_for(driver, By.ID, "task-table")
            edit_btn = driver.find_element(By.CSS_SELECTOR, "[id^='edit-btn-']")
            edit_btn.click()
            wait_for(driver, By.ID, "edit-task-form")
            Select(driver.find_element(By.ID, "priority")).select_by_value("high")
            driver.find_element(By.ID, "update-task-btn").click()
            wait_for(driver, By.ID, "task-table")
            assert "high" in driver.page_source
        finally:
            driver.quit()


class TestFiltersAndSearch:
    """TC-16 to TC-18: Filtering and searching tasks."""

    # ── TC-16 ─────────────────────────────────────────────────────────────────
    def test_16_filter_pending_tasks(self):
        """TC-16: 'Pending' filter shows only pending tasks."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            driver.get(f"{BASE_URL}/task/add")
            driver.find_element(By.ID, "title").send_keys("Pending Filter Task")
            driver.find_element(By.ID, "submit-task-btn").click()
            wait_for(driver, By.ID, "filter-bar")
            driver.find_element(By.ID, "filter-pending").click()
            time.sleep(0.5)
            assert "status=pending" in driver.current_url
            assert "pending" in driver.page_source
        finally:
            driver.quit()

    # ── TC-17 ─────────────────────────────────────────────────────────────────
    def test_17_search_finds_task_by_title(self):
        """TC-17: Searching by title keyword returns matching task."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            driver.get(f"{BASE_URL}/task/add")
            driver.find_element(By.ID, "title").send_keys("UniqueSearchKeyword999")
            driver.find_element(By.ID, "submit-task-btn").click()
            driver.get(f"{BASE_URL}/search")
            driver.find_element(By.ID, "search-input").send_keys("UniqueSearchKeyword999")
            driver.find_element(By.ID, "search-btn").click()
            wait_for(driver, By.ID, "search-results")
            assert "UniqueSearchKeyword999" in driver.page_source
        finally:
            driver.quit()

    # ── TC-18 ─────────────────────────────────────────────────────────────────
    def test_18_search_no_results_message(self):
        """TC-18: Searching for a non-existent title shows 'No results found'."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            driver.get(f"{BASE_URL}/search")
            driver.find_element(By.ID, "search-input").send_keys("XYZNOTEXIST12345")
            driver.find_element(By.ID, "search-btn").click()
            time.sleep(0.5)
            assert "No results found" in driver.page_source or "0 result" in driver.page_source
        finally:
            driver.quit()


class TestProfileAndLogout:
    """TC-19 to TC-20: Profile update and logout."""

    # ── TC-19 ─────────────────────────────────────────────────────────────────
    def test_19_profile_page_shows_username(self):
        """TC-19: Profile page displays the current user's username."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            driver.get(f"{BASE_URL}/profile")
            wait_for(driver, By.ID, "profile-username")
            username_el = driver.find_element(By.ID, "profile-username")
            assert TEST_USER in username_el.text
        finally:
            driver.quit()

    # ── TC-20 ─────────────────────────────────────────────────────────────────
    def test_20_logout_redirects_to_login(self):
        """TC-20: Clicking Logout redirects user to the Login page."""
        driver = get_driver()
        try:
            register_user(driver)
            login_user(driver)
            wait_for(driver, By.ID, "dashboard-heading")
            driver.get(f"{BASE_URL}/logout")
            time.sleep(0.7)
            assert "/login" in driver.current_url
            assert "login" in driver.page_source.lower()
        finally:
            driver.quit()
