<div align="center">
  
  # 💰 FinTrack — Enterprise Personal Finance Tracker

  <p align="center">
    A full-stack, production-grade personal finance management web application & REST API built with Python, Flask, SQLAlchemy, and MySQL.
  </p>

  <!-- Badges -->
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version" />
    <img src="https://img.shields.io/badge/Flask-3.1.1-lightgrey.svg" alt="Flask Version" />
    <img src="https://img.shields.io/badge/MySQL-8.0+-orange.svg" alt="MySQL Version" />
    <img src="https://img.shields.io/badge/Security-CSRF%20%26%20IDOR%20Protected-brightgreen.svg" alt="Security" />
    <img src="https://img.shields.io/badge/Tests-Pytest%20100%25%20Passing-success.svg" alt="Tests" />
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
  </p>

  <h3>
    <a href="#live-demo">Live Demo</a>
    <span> | </span>
    <a href="#features">Features</a>
    <span> | </span>
    <a href="#rest-api">REST API</a>
    <span> | </span>
    <a href="#security--architecture">Security</a>
    <span> | </span>
    <a href="#installation--docker">Setup & Docker</a>
    <span> | </span>
    <a href="#testing">Tests</a>
  </h3>
</div>

<br />

## 📸 Screenshots

| Dashboard Overview | Monthly Analytics |
| :---: | :---: |
| <img src="docs/dashboard.png" width="400" alt="Dashboard Overview" /> | <img src="docs/reports.png" width="400" alt="Monthly Analytics" /> |

<br />

## 🚀 Live Demo

You can interact with the live, production-deployed version of **FinTrack** here:  
👉 **[FinTrack Live Demo](https://personal-finance-tracker-l1n2.onrender.com)**

---

## 📖 Project Overview

FinTrack is an enterprise-grade financial management system designed for maximum security, real-time analytics, and high-precision financial tracking. Moving beyond simple spreadsheet tools, this application implements a fully normalized relational database, zero floating-point rounding errors through **Python `Decimal` arithmetic**, and strict **IDOR & CSRF defense mechanisms**.

The project is built on the **Flask Application Factory pattern** with modular Blueprints, an automated **Pytest** test suite, continuous integration (**GitHub Actions CI**), and complete containerization (**Docker & Docker Compose**).

---

## ✨ Features

- **📊 Real-time Dashboard**: Interactive summaries of income, expenses, net savings, and category-wise spending using Chart.js with optimized $O(1)$ grouped SQL queries.
- **✉️ Email OTP Account Verification**: Stops fake/unauthorized signups. Every new user must verify a time-sensitive 6-digit OTP sent to their email before their account is activated.
- **🔑 Forgot Password via OTP**: Secure password recovery via encrypted 6-digit verification codes sent directly to the account email.
- **🛡️ Dedicated Admin Portal**: Exclusive management panel for `tabrasali7@gmail.com` to view all platform metrics, audit users, monitor transactions, and manage accounts.
- **🔄 Account-to-Account Transfers**: Atomically transfer funds between accounts (e.g. Bank to Cash or Wallet) without distorting income/expense analytics.
- **🎯 Dedicated Budget Planner**: Set category thresholds with real-time visual spend progress bars, warning flags (>80%), and over-budget alerts.
- **🛡️ Enterprise Security**: Protected by CSRF tokens on all POST endpoints, Flask-Limiter brute-force protection, and strict Insecure Direct Object Reference (IDOR) checks.
- **💳 Multi-Account Net Worth Tracking**: Monitor balances across Bank Accounts, Credit Cards, Cash, and Digital Wallets.
- **🏷️ Smart Categorization**: 14+ default categories auto-seeded with 4-byte UTF-8 emoji and custom hex palette support.
- **📉 Financial Reporting**: Month-over-month comparisons, top 5 expenses, and automated savings rate calculations.
- **📥 CSV Data Export**: Export filtered transaction logs with custom timestamps for external audits and accounting.
- **🔌 RESTful JSON API**: Programmatic `/api/v1/` endpoints for headless integrations and mobile clients.

---

## 🔌 REST API Endpoints

FinTrack includes a decoupled REST API blueprint (`/api/v1`) exempt from CSRF tokens for seamless programmatic integration:

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | System and database connectivity health check | No |
| `GET` | `/api/v1/summary` | Monthly financial aggregations and account balances | Yes |
| `GET` | `/api/v1/transactions` | Paginated transaction history with optional filters | Yes |
| `GET` | `/api/v1/categories` | User-defined category listing with metadata | Yes |

---

## 🛡️ Security & Architecture

1. **CSRF Token Validation**: Enforced globally across all state-mutating requests via `Flask-WTF`.
2. **IDOR Mitigation**: All database operations verify resource ownership against `current_user.id` to prevent unauthorized cross-account modifications.
3. **High-Precision Currency Math**: Uses Python's `Decimal` alongside MySQL's `NUMERIC(15, 2)` to eliminate binary floating-point rounding errors.
4. **Rate Limiting**: Defends authentication endpoints against dictionary attacks using `Flask-Limiter`.
5. **Modern SQL Performance**: Eliminates N+1 query patterns using indexed multi-column `GROUP BY` aggregations.
6. **Branded Dark-Mode Error Handling**: Custom error pages for `400 Bad Request`, `403 Forbidden`, `404 Not Found`, `429 Rate Limit`, and `500 Server Error`.

---

## 🛠️ Tech Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: Flask (Application Factory, Blueprints)
- **Database & ORM**: MySQL 8.0+, SQLAlchemy, Flask-Migrate (Alembic)
- **Security**: Flask-Login, Flask-WTF (CSRF), Flask-Limiter, Werkzeug Security
- **Server**: Gunicorn WSGI

### Frontend
- **Templating**: Jinja2, HTML5
- **Styling**: Vanilla CSS3 (Custom Dark Theme, Glassmorphism, CSS Grid & Flexbox)
- **Interactivity**: Vanilla JavaScript, Chart.js

### DevOps & Testing
- **Testing**: Pytest, Pytest-Flask
- **CI/CD**: GitHub Actions
- **Containers**: Docker, Docker Compose

---

## ⚙️ Installation & Setup

### Option A: Running with Docker (Recommended)
You can launch both the web application and MySQL container with a single command:
```bash
docker compose up --build
```
The application will be live at `http://localhost:5000`.

---

### Option B: Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/md-rounaq-ali/personal-finance-tracker.git
   cd personal-finance-tracker
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the root directory:
   ```env
   FLASK_APP=run.py
   SECRET_KEY=your_secret_key_here
   DATABASE_URL=mysql+pymysql://root:password@localhost:3306/personal_finance_tracker?charset=utf8mb4

   # Email SMTP Configuration for live OTP delivery (e.g. Gmail)
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_16_char_gmail_app_password
   ```

5. **Run database migrations:**
   ```bash
   flask db upgrade
   ```

6. **Start development server:**
   ```bash
   python run.py
   ```

---

## 🧪 Testing

Run the automated test suite covering models, authentication, transaction math, and API endpoints:
```bash
pytest tests/ -v
```

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
