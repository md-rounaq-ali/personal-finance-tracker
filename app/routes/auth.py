"""
Authentication Routes — Login, Register with Email OTP, Forgot Password with OTP, Logout
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy import func
from app import db, limiter
from app.models import User, Category, Account
from app.utils.email_service import create_and_send_otp, verify_otp_code

auth_bp = Blueprint('auth', __name__)

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
    {'name': 'Transfer', 'type': 'expense', 'icon': '🔄', 'color': '#38bdf8'},
    {'name': 'Other', 'type': 'expense', 'icon': '📦', 'color': '#64748b'},
]


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("15 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        login_identifier = (request.form.get('email') or request.form.get('username') or '').strip().lower()
        password = request.form.get('password', '')

        # Lookup primarily by email (or username fallback)
        user = User.query.filter(
            (func.lower(User.email) == login_identifier) | 
            (func.lower(User.username) == login_identifier)
        ).first()

        if user and user.check_password(password):
            login_user(user, remember=bool(request.form.get('remember')))
            next_page = request.args.get('next')
            flash('Welcome back! 👋', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Input validation
        errors = []
        if len(username) < 3 or len(username) > 50:
            errors.append('Username must be between 3 and 50 characters.')
        if '@' not in email or '.' not in email:
            errors.append('Please enter a valid email address.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken.')
        if User.query.filter_by(email=email).first():
            errors.append('Email is already registered. Please sign in or reset your password.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')

        # Store pending registration temporarily in session
        session['pending_registration'] = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password)
        }

        # Send 6-digit verification OTP
        success, dev_or_err = create_and_send_otp(email, purpose='register')
        if not success:
            flash(f"Could not send email: {dev_or_err}. Please check your email settings.", 'error')
            return render_template('auth/register.html')

        if dev_or_err:
            flash(f"Verification code sent! (Local Dev OTP: {dev_or_err})", 'info')
        else:
            flash(f"A 6-digit verification code has been sent to {email}. Please check your inbox.", 'info')

        return redirect(url_for('auth.verify_registration_otp'))

    return render_template('auth/register.html')


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
@limiter.limit("15 per minute")
def verify_registration_otp():
    pending = session.get('pending_registration')
    if not pending:
        flash('Registration session expired. Please register again.', 'error')
        return redirect(url_for('auth.register'))

    email = pending.get('email')

    if request.method == 'POST':
        otp_code = request.form.get('otp', '').strip()

        is_valid, error_msg = verify_otp_code(email, otp_code, purpose='register')
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('auth/verify_otp.html', email=email)

        # OTP verified! Create user in database
        is_admin_user = (email.lower() == 'tabrasali7@gmail.com')
        user = User(
            username=pending['username'],
            email=email,
            password_hash=pending['password_hash'],
            is_admin=is_admin_user,
            is_verified=True
        )
        db.session.add(user)
        db.session.flush()

        # Seed categories
        for cat_data in DEFAULT_CATEGORIES:
            category = Category(user_id=user.id, **cat_data)
            db.session.add(category)

        # Seed default Cash account
        default_account = Account(
            user_id=user.id,
            name='Cash',
            type='cash',
            balance=0.00
        )
        db.session.add(default_account)
        db.session.commit()

        # Clear session
        session.pop('pending_registration', None)

        login_user(user)
        flash('Email verified and account created successfully! 🎉', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/verify_otp.html', email=email)


@auth_bp.route('/resend-otp', methods=['POST'])
@limiter.limit("3 per minute")
def resend_otp():
    purpose = request.form.get('purpose', 'register')
    email = None

    if purpose == 'register':
        pending = session.get('pending_registration')
        if pending:
            email = pending.get('email')
    elif purpose == 'forgot_password':
        email = session.get('reset_password_email')

    if not email:
        flash('Session expired. Please restart the request.', 'error')
        return redirect(url_for('auth.login'))

    success, dev_or_err = create_and_send_otp(email, purpose=purpose)
    if not success:
        flash(f"Could not deliver code: {dev_or_err}", 'error')
    elif dev_or_err:
        flash(f"A new verification code was generated! (Local Dev OTP: {dev_or_err})", 'info')
    else:
        flash(f"A new verification code was sent to {email}.", 'success')

    if purpose == 'register':
        return redirect(url_for('auth.verify_registration_otp'))
    return redirect(url_for('auth.reset_password'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        user = User.query.filter_by(email=email).first()
        if user:
            session['reset_password_email'] = email
            success, dev_or_err = create_and_send_otp(email, purpose='forgot_password')
            if not success:
                flash(f"Could not send email: {dev_or_err}", 'error')
                return render_template('auth/forgot_password.html')

            if dev_or_err:
                flash(f"Password reset code generated! (Local Dev OTP: {dev_or_err})", 'info')
            else:
                flash(f"A 6-digit password reset code has been sent to {email}.", 'info')
            return redirect(url_for('auth.reset_password'))
        else:
            # Subtle defense: don't reveal if email exists or not, but give feedback
            flash(f"If an account is associated with {email}, you will receive a reset code.", 'info')
            return render_template('auth/forgot_password.html')

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def reset_password():
    email = session.get('reset_password_email')
    if not email:
        flash('Password reset session expired. Please start again.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        otp_code = request.form.get('otp', '').strip()
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('auth/reset_password.html', email=email)

        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', email=email)

        is_valid, error_msg = verify_otp_code(email, otp_code, purpose='forgot_password')
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('auth/reset_password.html', email=email)

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User account not found.', 'error')
            return redirect(url_for('auth.login'))

        user.set_password(new_password)
        db.session.commit()

        session.pop('reset_password_email', None)
        flash('Password reset successfully! You can now sign in with your new password. 🔐', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', email=email)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
