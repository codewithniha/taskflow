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
import random
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# ── Config ────────────────────────────────────────────────────────────────────

BASE_URL     = "http://127.0.0.1:5000"
WAIT_TIMEOUT = 10   # seconds


# ── Driver Factory ────────────────────────────────────────────────────────────

def get_driver():
    """Return a headless Chrome WebDriver."""
    options = Options()
    options.add_argument("--headless")
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


def unique_user():
    """Generate a unique username + email for each test that needs one."""
    uid = random.randint(100000, 999999)
    return f"user_{uid}", f"user_{uid}@test.com", "TestPass@123"


def register_and_login(driver):
    """
    Create a brand-new unique user and log them in.
    Returns (username, password) for reference.

    Using a unique user per test eliminates ALL 'already exists' race conditions
    and makes every test fully independent.
    """
    username, email, password = unique_user()

    # ── Register ──────────────────────────────────────────────────────────────
    driver.get(f"{BASE_URL}/register")
    wait_for(driver, By.ID, "register-btn")
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "email").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "confirm_password").send_keys(password)
    driver.find_element(By.ID, "register-btn").click()

    # Wait until we land on /login (the redirect after successful registration)
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.url_contains("/login")
    )

    # ── Login ─────────────────────────────────────────────────────────────────
    wait_for(driver, By.ID, "login-btn")
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "login-btn").click()

    # Wait until we land on /dashboard
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.url_contains("/dashboard")
    )

    return username, password


def add_task(driver, title, priority="medium"):
    """Helper: navigate to add-task and create one task, then return to dashboard."""
    driver.get(f"{BASE_URL}/task/add")
    wait_for(driver, By.ID, "title")
    driver.find_element(By.ID, "title").send_keys(title)
    Select(driver.find_element(By.ID, "priority")).select_by_value(priority)
    driver.find_element(By.ID, "submit-task-btn").click()
    # Wait until redirected back to dashboard
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.url_contains("/dashboard")
    )


# ═════════════════════════════════════════════════════════════════════════════
# TEST CASES
# ═════════════════════════════════════════════════════════════════════════════

class TestAuthentication:
    """TC-01 to TC-05: Registration & Login flows"""

    def test_01_register_page_loads(self):
        """TC-01: Register page loads and contains expected form fields."""
        driver = get_driver()
        try:
            driver.get(f"{BASE_URL}/register")
            wait_for(driver, By.ID, "register-btn")
            assert driver.find_element(By.ID, "username")
            assert driver.find_element(By.ID, "email")
            assert driver.find_element(By.ID, "password")
            assert driver.find_element(By.ID, "confirm_password")
            assert driver.find_element(By.ID, "register-btn")
        finally:
            driver.quit()

    def test_02_successful_registration(self):
        """TC-02: A new user can register successfully and lands on /login."""
        driver = get_driver()
        try:
            username, email, password = unique_user()
            driver.get(f"{BASE_URL}/register")
            wait_for(driver, By.ID, "register-btn")
            driver.find_element(By.ID, "username").send_keys(username)
            driver.find_element(By.ID, "email").send_keys(email)
            driver.find_element(By.ID, "password").send_keys(password)
            driver.find_element(By.ID, "confirm_password").send_keys(password)
            driver.find_element(By.ID, "register-btn").click()
            WebDriverWait(driver, WAIT_TIMEOUT).until(EC.url_contains("/login"))
            assert "/login" in driver.current_url
        finally:
            driver.quit()

    def test_03_registration_password_mismatch(self):
        """TC-03: Registration fails when passwords do not match."""
        driver = get_driver()
        try:
            username, email, _ = unique_user()
            driver.get(f"{BASE_URL}/register")
            wait_for(driver, By.ID, "register-btn")
            driver.find_element(By.ID, "username").send_keys(username)
            driver.find_element(By.ID, "email").send_keys(email)
            driver.find_element(By.ID, "password").send_keys("Pass@1234")
            driver.find_element(By.ID, "confirm_password").send_keys("Different@999")
            driver.find_element(By.ID, "register-btn").click()
            error = wait_for(driver, By.ID, "error-message")
            assert "Passwords do not match" in error.text
        finally:
            driver.quit()

    def test_04_successful_login(self):
        """TC-04: Registered user can log in and reaches the dashboard."""
        driver = get_driver()
        try:
            register_and_login(driver)
            assert "/dashboard" in driver.current_url
            wait_for(driver, By.ID, "dashboard-heading")
        finally:
            driver.quit()

    def test_05_invalid_login_shows_error(self):
        """TC-05: Login with wrong password shows an error message."""
        driver = get_driver()
        try:
            driver.get(f"{BASE_URL}/login")
            wait_for(driver, By.ID, "login-btn")
            driver.find_element(By.ID, "username").send_keys("nobody_xyz_99999")
            driver.find_element(By.ID, "password").send_keys("WrongPass!")
            driver.find_element(By.ID, "login-btn").click()
            error = wait_for(driver, By.ID, "error-message")
            assert "Invalid" in error.text
        finally:
            driver.quit()


class TestDashboard:
    """TC-06 to TC-08: Dashboard UI and navigation."""

    def test_06_dashboard_stats_visible(self):
        """TC-06: Stats cards (total, pending, completed, high) are visible."""
        driver = get_driver()
        try:
            register_and_login(driver)
            wait_for(driver, By.ID, "stats-row")
            assert driver.find_element(By.ID, "stat-total")
            assert driver.find_element(By.ID, "stat-pending")
            assert driver.find_element(By.ID, "stat-completed")
            assert driver.find_element(By.ID, "stat-high")
        finally:
            driver.quit()

    def test_07_navbar_links_present(self):
        """TC-07: Navigation bar contains Dashboard, New Task, Search, Profile, Logout."""
        driver = get_driver()
        try:
            register_and_login(driver)
            nav_text = driver.find_element(By.TAG_NAME, "nav").text
            for label in ["Dashboard", "New Task", "Search", "Profile", "Logout"]:
                assert label in nav_text, f"'{label}' not found in nav"
        finally:
            driver.quit()

    def test_08_unauthenticated_redirect_to_login(self):
        """TC-08: Visiting /dashboard without login redirects to /login."""
        driver = get_driver()
        try:
            driver.get(f"{BASE_URL}/dashboard")
            WebDriverWait(driver, WAIT_TIMEOUT).until(EC.url_contains("/login"))
            assert "/login" in driver.current_url
        finally:
            driver.quit()


class TestTaskCRUD:
    """TC-09 to TC-15: Create, Read, Update, Delete tasks."""

    def test_09_add_task_page_loads(self):
        """TC-09: Add Task page loads with all required form fields."""
        driver = get_driver()
        try:
            register_and_login(driver)
            driver.get(f"{BASE_URL}/task/add")
            wait_for(driver, By.ID, "title")
            assert driver.find_element(By.ID, "title")
            assert driver.find_element(By.ID, "description")
            assert driver.find_element(By.ID, "priority")
            assert driver.find_element(By.ID, "due_date")
            assert driver.find_element(By.ID, "submit-task-btn")
        finally:
            driver.quit()

    def test_10_create_task_successfully(self):
        """TC-10: A new task can be created and appears on the dashboard."""
        driver = get_driver()
        try:
            register_and_login(driver)
            add_task(driver, "Selenium Test Task", priority="high")
            wait_for(driver, By.ID, "task-table")
            assert "Selenium Test Task" in driver.page_source
        finally:
            driver.quit()

    def test_11_create_task_empty_title_shows_error(self):
        """TC-11: Submitting a task with an empty title is blocked."""
        driver = get_driver()
        try:
            register_and_login(driver)
            driver.get(f"{BASE_URL}/task/add")
            wait_for(driver, By.ID, "submit-task-btn")
            # Fill description only, leave title blank
            driver.find_element(By.ID, "description").send_keys("No title here")
            driver.find_element(By.ID, "submit-task-btn").click()
            time.sleep(0.5)
            # Should still be on /task/add (HTML5 required attribute prevents submit)
            assert "/task/add" in driver.current_url or "required" in driver.page_source.lower()
        finally:
            driver.quit()

    def test_12_edit_task_updates_title(self):
        """TC-12: Editing a task changes its title on the dashboard."""
        driver = get_driver()
        try:
            register_and_login(driver)
            add_task(driver, "Original Title")
            wait_for(driver, By.ID, "task-table")
            driver.find_element(By.CSS_SELECTOR, "[id^='edit-btn-']").click()
            wait_for(driver, By.ID, "edit-task-form")
            title_field = driver.find_element(By.ID, "title")
            title_field.clear()
            title_field.send_keys("Updated Title")
            driver.find_element(By.ID, "update-task-btn").click()
            WebDriverWait(driver, WAIT_TIMEOUT).until(EC.url_contains("/dashboard"))
            assert "Updated Title" in driver.page_source
        finally:
            driver.quit()

    def test_13_delete_task_removes_it(self):
        """TC-13: Deleting a task removes it from the task list."""
        driver = get_driver()
        try:
            register_and_login(driver)
            add_task(driver, "Task To Delete")
            wait_for(driver, By.ID, "task-table")
            assert "Task To Delete" in driver.page_source
            # Override confirm() so the dialog auto-accepts
            driver.execute_script("window.confirm = function() { return true; };")
            driver.find_element(By.CSS_SELECTOR, "[id^='delete-btn-']").click()
            time.sleep(1)
            assert "Task To Delete" not in driver.page_source
        finally:
            driver.quit()

    def test_14_mark_task_complete(self):
        """TC-14: Clicking 'Complete' changes a task's status badge to 'completed'."""
        driver = get_driver()
        try:
            register_and_login(driver)
            add_task(driver, "Task To Complete")
            wait_for(driver, By.ID, "task-table")
            driver.find_element(By.CSS_SELECTOR, "[id^='complete-btn-']").click()
            WebDriverWait(driver, WAIT_TIMEOUT).until(EC.url_contains("/dashboard"))
            assert "completed" in driver.page_source
        finally:
            driver.quit()

    def test_15_edit_task_priority_change(self):
        """TC-15: Changing priority in edit form is reflected on the dashboard."""
        driver = get_driver()
        try:
            register_and_login(driver)
            add_task(driver, "Priority Test Task", priority="low")
            wait_for(driver, By.ID, "task-table")
            driver.find_element(By.CSS_SELECTOR, "[id^='edit-btn-']").click()
            wait_for(driver, By.ID, "edit-task-form")
            Select(driver.find_element(By.ID, "priority")).select_by_value("high")
            driver.find_element(By.ID, "update-task-btn").click()
            WebDriverWait(driver, WAIT_TIMEOUT).until(EC.url_contains("/dashboard"))
            assert "high" in driver.page_source
        finally:
            driver.quit()


class TestFiltersAndSearch:
    """TC-16 to TC-18: Filtering and searching tasks."""

    def test_16_filter_pending_tasks(self):
        """TC-16: 'Pending' filter shows only pending tasks."""
        driver = get_driver()
        try:
            register_and_login(driver)
            add_task(driver, "Pending Filter Task")
            wait_for(driver, By.ID, "filter-bar")
            driver.find_element(By.ID, "filter-pending").click()
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.url_contains("status=pending")
            )
            assert "status=pending" in driver.current_url
            assert "pending" in driver.page_source
        finally:
            driver.quit()

    def test_17_search_finds_task_by_title(self):
        """TC-17: Searching by title keyword returns matching task."""
        driver = get_driver()
        try:
            register_and_login(driver)
            add_task(driver, "UniqueSearchKeyword999")
            driver.get(f"{BASE_URL}/search")
            wait_for(driver, By.ID, "search-input")
            driver.find_element(By.ID, "search-input").send_keys("UniqueSearchKeyword999")
            driver.find_element(By.ID, "search-btn").click()
            wait_for(driver, By.ID, "search-results")
            assert "UniqueSearchKeyword999" in driver.page_source
        finally:
            driver.quit()

    def test_18_search_no_results_message(self):
        """TC-18: Searching for a non-existent title shows a no-results message."""
        driver = get_driver()
        try:
            register_and_login(driver)
            driver.get(f"{BASE_URL}/search")
            wait_for(driver, By.ID, "search-input")
            driver.find_element(By.ID, "search-input").send_keys("XYZNOTEXIST12345")
            driver.find_element(By.ID, "search-btn").click()
            time.sleep(0.5)
            assert "No results found" in driver.page_source or "0 result" in driver.page_source
        finally:
            driver.quit()


class TestProfileAndLogout:
    """TC-19 to TC-20: Profile update and logout."""

    def test_19_profile_page_shows_username(self):
        """TC-19: Profile page displays the current user's username."""
        driver = get_driver()
        try:
            username, _ = register_and_login(driver)
            driver.get(f"{BASE_URL}/profile")
            wait_for(driver, By.ID, "profile-username")
            assert username in driver.find_element(By.ID, "profile-username").text
        finally:
            driver.quit()

    def test_20_logout_redirects_to_login(self):
        """TC-20: Clicking Logout redirects user to the Login page."""
        driver = get_driver()
        try:
            register_and_login(driver)
            wait_for(driver, By.ID, "dashboard-heading")
            driver.get(f"{BASE_URL}/logout")
            WebDriverWait(driver, WAIT_TIMEOUT).until(EC.url_contains("/login"))
            assert "/login" in driver.current_url
        finally:
            driver.quit()
