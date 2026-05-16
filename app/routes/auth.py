"""
Authentication Routes — Login, Register, Logout
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Category, Account

auth_bp = Blueprint('auth', __name__)

# Default categories seeded on registration
DEFAULT_CATEGORIES = [
    {'name': 'Salary', 'type': 'income', 'icon': '💼', 'color': '#10b981'},
    {'name': 'Freelance', 'type': 'income', 'icon': '💻', 'color': '#06b6d4'},
    {'name': 'Investments', 'type': 'income', 'icon': '📈', 'color': '#8b5cf6'},
    {'name': 'Other Income', 'type': 'income', 'icon': '💵', 'color': '#14b8a6'},
    {'name': 'Groceries', 'type': 'expense', 'icon': '🛒', 'color': '#f43f5e'},
    {'name': 'Rent', 'type': 'expense', 'icon': '🏠', 'color': '#ef4444'},
    {'name': 'Utilities', 'type': 'expense', 'icon': '💡', 'color': '#f97316'},
    {'name': 'Transport', 'type': 'expense', 'icon': '🚗', 'color': '#eab308'},
    {'name': 'Food & Dining', 'type': 'expense', 'icon': '🍕', 'color': '#ec4899'},
    {'name': 'Entertainment', 'type': 'expense', 'icon': '🎬', 'color': '#a855f7'},
    {'name': 'Shopping', 'type': 'expense', 'icon': '🛍️', 'color': '#6366f1'},
    {'name': 'Healthcare', 'type': 'expense', 'icon': '🏥', 'color': '#14b8a6'},
    {'name': 'Education', 'type': 'expense', 'icon': '📚', 'color': '#0ea5e9'},
    {'name': 'Other', 'type': 'expense', 'icon': '📦', 'color': '#64748b'},
]


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember'))
            next_page = request.args.get('next')
            flash('Welcome back! 👋', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        errors = []
        if len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if '@' not in email:
            errors.append('Please enter a valid email address.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')

        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Get user.id before committing

        # Seed default categories
        for cat_data in DEFAULT_CATEGORIES:
            category = Category(user_id=user.id, **cat_data)
            db.session.add(category)

        # Create default Cash account
        default_account = Account(
            user_id=user.id,
            name='Cash',
            type='cash',
            balance=0.00
        )
        db.session.add(default_account)

        db.session.commit()
        login_user(user)
        flash('Account created successfully! 🎉', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
