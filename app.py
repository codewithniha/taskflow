from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'selenium-test-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskmanager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ── Models ──────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80),  unique=True, nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password     = db.Column(db.String(200), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    tasks        = db.relationship('Task', backref='owner', lazy=True, cascade='all, delete-orphan')

class Task(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    priority    = db.Column(db.String(20), default='medium')   # low / medium / high
    status      = db.Column(db.String(20), default='pending')  # pending / completed
    due_date    = db.Column(db.String(20), default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ── Auth helpers ─────────────────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# ── Register ─────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not username or not email or not password:
            error = 'All fields are required.'
        elif len(username) < 3:
            error = 'Username must be at least 3 characters.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif User.query.filter_by(username=username).first():
            error = 'Username already exists.'
        elif User.query.filter_by(email=email).first():
            error = 'Email already registered.'
        else:
            user = User(username=username, email=email,
                        password=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

# ── Login ─────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        error = 'Invalid username or password.'
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    filter_status   = request.args.get('status', 'all')
    filter_priority = request.args.get('priority', 'all')
    query = Task.query.filter_by(user_id=current_user.id)
    if filter_status != 'all':
        query = query.filter_by(status=filter_status)
    if filter_priority != 'all':
        query = query.filter_by(priority=filter_priority)
    tasks = query.order_by(Task.created_at.desc()).all()
    stats = {
        'total':     Task.query.filter_by(user_id=current_user.id).count(),
        'pending':   Task.query.filter_by(user_id=current_user.id, status='pending').count(),
        'completed': Task.query.filter_by(user_id=current_user.id, status='completed').count(),
        'high':      Task.query.filter_by(user_id=current_user.id, priority='high').count(),
    }
    return render_template('dashboard.html', tasks=tasks, stats=stats,
                           filter_status=filter_status, filter_priority=filter_priority)

# ── Add Task ──────────────────────────────────────────────────────────────────

@app.route('/task/add', methods=['GET', 'POST'])
@login_required
def add_task():
    error = None
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority    = request.form.get('priority', 'medium')
        due_date    = request.form.get('due_date', '')
        if not title:
            error = 'Task title is required.'
        elif len(title) < 3:
            error = 'Title must be at least 3 characters.'
        else:
            task = Task(title=title, description=description,
                        priority=priority, due_date=due_date,
                        user_id=current_user.id)
            db.session.add(task)
            db.session.commit()
            flash('Task created successfully!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('add_task.html', error=error)

# ── Edit Task ─────────────────────────────────────────────────────────────────

@app.route('/task/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    error = None
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority    = request.form.get('priority', 'medium')
        due_date    = request.form.get('due_date', '')
        status      = request.form.get('status', 'pending')
        if not title:
            error = 'Task title is required.'
        else:
            task.title       = title
            task.description = description
            task.priority    = priority
            task.due_date    = due_date
            task.status      = status
            db.session.commit()
            flash('Task updated successfully!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('edit_task.html', task=task, error=error)

# ── Delete Task ───────────────────────────────────────────────────────────────

@app.route('/task/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted.', 'info')
    return redirect(url_for('dashboard'))

# ── Complete Toggle ───────────────────────────────────────────────────────────

@app.route('/task/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.status = 'completed' if task.status == 'pending' else 'pending'
    db.session.commit()
    return redirect(url_for('dashboard'))

# ── Profile ───────────────────────────────────────────────────────────────────

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    error   = None
    success = None
    if request.method == 'POST':
        new_email = request.form.get('email', '').strip()
        new_pass  = request.form.get('new_password', '')
        confirm   = request.form.get('confirm_password', '')
        if not new_email:
            error = 'Email is required.'
        elif new_pass and new_pass != confirm:
            error = 'Passwords do not match.'
        else:
            current_user.email = new_email
            if new_pass:
                current_user.password = generate_password_hash(new_pass)
            db.session.commit()
            success = 'Profile updated successfully!'
    return render_template('profile.html', error=error, success=success)

# ── Search ────────────────────────────────────────────────────────────────────

@app.route('/search')
@login_required
def search():
    q     = request.args.get('q', '').strip()
    tasks = []
    if q:
        tasks = Task.query.filter(
            Task.user_id == current_user.id,
            Task.title.ilike(f'%{q}%')
        ).all()
    return render_template('search.html', tasks=tasks, query=q)

# ── Init DB ───────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
