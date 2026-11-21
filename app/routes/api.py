"""
REST API Blueprint — Clean JSON endpoints for programmatic integration
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from datetime import date
from decimal import Decimal
from app import db
from app.models import Transaction, Account, Category

api_bp = Blueprint('api', __name__)


@api_bp.route('/health', methods=['GET'])
def health():
    """Service health check endpoint"""
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return jsonify({
        "status": "online",
        "service": "FinTrack API",
        "version": "1.0.0",
        "database": db_status
    }), 200


@api_bp.route('/summary', methods=['GET'])
@login_required
def get_summary():
    """Retrieve monthly financial summary for authenticated user"""
    today = date.today()
    month = request.args.get('month', today.month, type=int)
    year = request.args.get('year', today.year, type=int)

    totals = db.session.query(
        Transaction.type,
        func.coalesce(func.sum(Transaction.amount), 0).label('total')
    ).filter(
        Transaction.user_id == current_user.id,
        extract('month', Transaction.transaction_date) == month,
        extract('year', Transaction.transaction_date) == year
    ).group_by(Transaction.type).all()

    totals_dict = {t.type: float(t.total) for t in totals}
    income = totals_dict.get('income', 0.0)
    expense = totals_dict.get('expense', 0.0)

    accounts = Account.query.filter_by(user_id=current_user.id).all()
    total_net_worth = sum((float(a.balance or 0) for a in accounts), 0.0)

    return jsonify({
        "month": month,
        "year": year,
        "income": income,
        "expense": expense,
        "net_savings": round(income - expense, 2),
        "total_net_worth": round(total_net_worth, 2),
        "accounts": [
            {
                "id": a.id,
                "name": a.name,
                "type": a.type,
                "balance": float(a.balance or 0)
            } for a in accounts
        ]
    }), 200


@api_bp.route('/transactions', methods=['GET'])
@login_required
def get_transactions():
    """List transactions with pagination and optional type filter"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    txn_type = request.args.get('type')

    query = Transaction.query.filter_by(user_id=current_user.id)
    if txn_type in ('income', 'expense'):
        query = query.filter(Transaction.type == txn_type)

    pagination = query.order_by(
        Transaction.transaction_date.desc(),
        Transaction.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
        "items": [
            {
                "id": t.id,
                "amount": float(t.amount),
                "type": t.type,
                "description": t.description,
                "date": t.transaction_date.isoformat(),
                "category": t.category.name if t.category else None,
                "account": t.account.name if t.account else None
            } for t in pagination.items
        ]
    }), 200


@api_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """List user categories"""
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "icon": c.icon,
                "color": c.color
            } for c in categories
        ]
    }), 200
