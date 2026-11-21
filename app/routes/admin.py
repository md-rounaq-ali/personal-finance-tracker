"""
Admin Panel Routes — Restricted strictly to tabrasali7@gmail.com and system administrators
"""
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import func, case
from app import db
from app.models import User, Transaction, Account, Category, Budget

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if not current_user.has_admin_access:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/admin')
@login_required
@admin_required
def index():
    # Platform-wide statistics
    total_users = User.query.count()
    total_transactions = Transaction.query.count()
    total_volume = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).scalar()
    total_accounts = Account.query.count()

    # Search & User listing
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = User.query
    if search_query:
        query = query.filter(
            (User.username.ilike(f'%{search_query}%')) | (User.email.ilike(f'%{search_query}%'))
        )

    # Root Admin and Admins are always pinned to the top of the list
    admin_priority = case(
        (func.lower(User.email) == 'tabrasali7@gmail.com', 1),
        (User.is_admin.is_(True), 2),
        else_=3
    )

    users_pagination = query.order_by(admin_priority, User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Compute per-user statistics for current page
    user_data = []
    for u in users_pagination.items:
        tx_count = Transaction.query.filter_by(user_id=u.id).count()
        acc_count = Account.query.filter_by(user_id=u.id).count()
        total_bal = db.session.query(
            func.coalesce(func.sum(Account.balance), 0)
        ).filter_by(user_id=u.id).scalar()

        user_data.append({
            'user': u,
            'transaction_count': tx_count,
            'account_count': acc_count,
            'total_balance': float(total_bal),
            'is_root_admin': (u.email.lower() == 'tabrasali7@gmail.com')
        })

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_transactions=total_transactions,
                           total_volume=float(total_volume),
                           total_accounts=total_accounts,
                           users=user_data,
                           pagination=users_pagination,
                           search=search_query)


@admin_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user_to_delete = db.session.get(User, user_id)
    if not user_to_delete:
        flash('User not found.', 'error')
        return redirect(url_for('admin.index'))

    # Prevent deleting the root administrator
    if user_to_delete.email.lower() == 'tabrasali7@gmail.com':
        flash('Cannot delete root system administrator (tabrasali7@gmail.com).', 'error')
        return redirect(url_for('admin.index'))

    # Prevent deleting own current session
    if user_to_delete.id == current_user.id:
        flash('Cannot delete your own active administrator account.', 'error')
        return redirect(url_for('admin.index'))

    username = user_to_delete.username
    db.session.delete(user_to_delete)
    db.session.commit()

    flash(f'User "{username}" and all associated data deleted successfully. 🗑️', 'success')
    return redirect(url_for('admin.index'))
