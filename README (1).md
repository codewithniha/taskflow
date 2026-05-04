# TaskFlow – Task Manager Web App + Selenium Test Suite

A complete Python/Flask task manager web application with a SQLite database and
20 automated Selenium test cases targeting headless Chrome.

---

## Project Structure

```
taskmanager/
├── app.py                  # Flask application (routes, models, DB)
├── requirements.txt        # Python dependencies
├── test_taskflow.py        # 20 Selenium test cases
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── add_task.html
│   ├── edit_task.html
│   ├── profile.html
│   └── search.html
└── taskmanager.db          # SQLite DB (auto-created on first run)
```

---

## Features of the Web Application

| Page        | Functionality                                             |
|-------------|-----------------------------------------------------------|
| Register    | New user signup with validation                          |
| Login       | Username + password authentication                        |
| Dashboard   | View all tasks, stats, filter by status / priority       |
| Add Task    | Create task with title, description, priority, due date  |
| Edit Task   | Update title, description, priority, status, due date    |
| Delete Task | Permanently remove a task (with confirm dialog)          |
| Complete    | Toggle task between pending / completed                  |
| Search      | Search tasks by title keyword                            |
| Profile     | Update email or password                                 |
| Logout      | End session and redirect to login                        |

**Database:** SQLite via SQLAlchemy  
**Auth:** Flask-Login (session-based)  
**Backend:** Python 3.8+ / Flask 3.0

---

## Setup & Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the web application

```bash
python app.py
```

The app runs at **http://127.0.0.1:5000**

### 3. Install ChromeDriver

The ChromeDriver version must match your installed Chrome browser.

```bash
# Ubuntu / EC2
sudo apt-get update
sudo apt-get install -y google-chrome-stable
# ChromeDriver is managed automatically by Selenium 4.6+
```

### 4. Run the Selenium tests

```bash
pytest test_taskflow.py -v
```

---

## Test Cases Summary

| #  | Class                    | Test ID | Description                                          |
|----|--------------------------|---------|------------------------------------------------------|
| 1  | TestAuthentication       | TC-01   | Register page loads with all form fields             |
| 2  | TestAuthentication       | TC-02   | Successful new user registration                     |
| 3  | TestAuthentication       | TC-03   | Registration fails on password mismatch              |
| 4  | TestAuthentication       | TC-04   | Successful login redirects to dashboard              |
| 5  | TestAuthentication       | TC-05   | Invalid credentials show error message               |
| 6  | TestDashboard            | TC-06   | Dashboard stats cards are visible                    |
| 7  | TestDashboard            | TC-07   | Navbar contains all expected links                   |
| 8  | TestDashboard            | TC-08   | Unauthenticated access to /dashboard redirects       |
| 9  | TestTaskCRUD             | TC-09   | Add Task page loads with correct form fields         |
| 10 | TestTaskCRUD             | TC-10   | Task is created and appears on dashboard             |
| 11 | TestTaskCRUD             | TC-11   | Empty title submission shows validation error        |
| 12 | TestTaskCRUD             | TC-12   | Editing a task updates its title on dashboard        |
| 13 | TestTaskCRUD             | TC-13   | Deleting a task removes it from the list             |
| 14 | TestTaskCRUD             | TC-14   | Marking a task complete changes its status badge     |
| 15 | TestTaskCRUD             | TC-15   | Editing priority is reflected on the dashboard       |
| 16 | TestFiltersAndSearch     | TC-16   | Pending filter shows only pending tasks              |
| 17 | TestFiltersAndSearch     | TC-17   | Search by title keyword returns matching task        |
| 18 | TestFiltersAndSearch     | TC-18   | Searching non-existent keyword shows no-results msg  |
| 19 | TestProfileAndLogout     | TC-19   | Profile page displays current user's username        |
| 20 | TestProfileAndLogout     | TC-20   | Logout redirects user to login page                  |

---

## Headless Chrome (Jenkins / AWS EC2)

All tests use headless Chrome by default via the `get_driver()` helper:

```python
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
```

### Jenkinsfile snippet

```groovy
pipeline {
    agent any
    stages {
        stage('Install') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Start App') {
            steps {
                sh 'nohup python app.py &'
                sh 'sleep 3'
            }
        }
        stage('Selenium Tests') {
            steps {
                sh 'pytest test_taskflow.py -v --junitxml=results.xml'
            }
        }
    }
    post {
        always {
            junit 'results.xml'
        }
    }
}
```

---

## Notes

- The SQLite database (`taskmanager.db`) is auto-created on first run.
- Each test registers its own user (or reuses one if already registered).
- Tests are fully independent — no shared global state between test classes.
- Selenium 4.6+ uses Selenium Manager to auto-download ChromeDriver; no manual path setup needed.
