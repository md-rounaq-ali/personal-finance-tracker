"""
Personal Finance Tracker — Application Factory
"""
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.transactions import transactions_bp
    from app.routes.categories import categories_bp
    from app.routes.accounts import accounts_bp
    from app.routes.reports import reports_bp
    from app.routes.budgets import budgets_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    # Exempt REST API from CSRF token requirements (API clients use JSON/Auth)
    csrf.exempt(api_bp)

    # Context processor — inject current year for templates
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return dict(current_year=datetime.now().year)

    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return render_template('errors/400.html', error=error), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html', error=error), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html', error=error), 404

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template('errors/429.html', error=e), 429

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html', error=error), 500

    return app
