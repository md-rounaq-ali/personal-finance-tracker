<div align="center">
  
  <img src="app/static/img/logo.svg" alt="FinTrack Logo" width="280" />

  # 💰 FinTrack — Enterprise Personal Finance & Budget Platform

  <p align="center">
    A production-grade personal finance management web application, responsive landing engine, and decoupled REST API engineered with <strong>Python, Flask, SQLAlchemy, MySQL, and Chart.js</strong>.
  </p>

  <!-- Badges -->
  <p align="center">
    <a href="https://personal-finance-tracker-l1n2.onrender.com"><img src="https://img.shields.io/badge/Live%20Demo-Online-success?style=for-the-badge&logo=render" alt="Live Demo" /></a>
    <a href="https://md-rounaq-ali.netlify.app/"><img src="https://img.shields.io/badge/Author-Md%20Rounaq%20Ali-06b6d4?style=for-the-badge" alt="Author" /></a>
    <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue?style=for-the-badge&logo=python" alt="Python Version" />
    <img src="https://img.shields.io/badge/MySQL-8.0%20(Clever%20Cloud)-orange?style=for-the-badge&logo=mysql" alt="MySQL Version" />
    <img src="https://img.shields.io/badge/Tests-23%20Passed%20(100%25)-brightgreen?style=for-the-badge&logo=pytest" alt="Tests" />
    <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
  </p>

  <h3>
    <a href="https://personal-finance-tracker-l1n2.onrender.com">🌐 Live Application</a>
    <span> &bull; </span>
    <a href="https://md-rounaq-ali.netlify.app/">👨‍💻 Developer Portfolio</a>
    <span> &bull; </span>
    <a href="#-key-features">Features</a>
    <span> &bull; </span>
    <a href="#-rest-api">REST API</a>
    <span> &bull; </span>
    <a href="#-security--architecture">Security</a>
    <span> &bull; </span>
    <a href="#-installation--setup">Setup</a>
  </h3>
</div>

<br />

---

## 📸 Application Showcase

| Public Responsive Landing Engine | Authenticated Financial Dashboard |
| :---: | :---: |
| <img src="app/static/img/og_banner.jpg" width="460" alt="FinTrack Hero Banner" /> | <img src="docs/dashboard.png" width="460" alt="Dashboard Overview" /> |

| Monthly Analytical Reports | Multi-Account & Category Budgets |
| :---: | :---: |
| <img src="docs/reports.png" width="460" alt="Monthly Analytics" /> | <img src="docs/dashboard.png" width="460" alt="Accounts & Budgets" /> |

<br />

---

## 🌐 Live Production Deployment

FinTrack is deployed 24/7 on high-availability cloud infrastructure:
- **Live URL**: [https://personal-finance-tracker-l1n2.onrender.com](https://personal-finance-tracker-l1n2.onrender.com)
- **Database**: Cloud MySQL 8.0 on **Clever Cloud** (European Datacenter)
- **Email Delivery**: HTTPS Port 443 Transactional Engine (**Brevo / Resend**)
- **Keep-Alive Uptime**: Automated ping cron-job via `/api/v1/health`

---

## 📖 Executive Summary

**FinTrack** is an enterprise-grade financial management platform engineered to deliver bank-grade security, real-time analytics, and precision wealth management. Moving beyond basic spreadsheets, FinTrack provides:

1. **Relational Double-Entry Integrity**: Powered by MySQL with strict foreign keys and ACID transactions.
2. **Zero Floating-Point Drift**: All currency computations execute using Python's `Decimal` type alongside MySQL's `NUMERIC(15, 2)` precision fields.
3. **Dual-Layer Defensive Security**: Protected against IDOR, CSRF, rate-limit brute-forcing, and unauthorized session tampering.
4. **Search Engine & PageRank Optimized**: Full Semantic HTML5, XML Sitemaps, Robots.txt, and Schema.org JSON-LD structured data linking creator **Md Rounaq Ali** to search entities.

---

## ✨ Key Features

### 🌟 Public Landing & Onboarding Engine
- **High-Converting Landing Page (`/`)**: Displays value propositions, live UI mockup cards, 6-pillar feature grid, architecture overview, and FAQ accordions.
- **Smart Authentication Router**: Automatically routes authenticated users straight to `/dashboard`.
- **Intelligent Login Fallback**: Unregistered users attempting login are automatically redirected to account creation with their email pre-filled.

### 💰 Financial Operations & Tracking
- **Smart Transaction Tracking**: Instant recording of Income, Expense, and atomic Account-to-Account Transfers.
- **Multi-Account Net Worth Hub**: Consolidate Bank Accounts, Cash Wallets, Savings, and Credit Cards in real-time.
- **Predictive Category Budgets**: Visual budget progress indicators with warning thresholds (>80%) and overspending flags.
- **Dynamic Chart.js Visualizations**: Cash flow distribution, top spending categories, and month-over-month comparisons.
- **CSV Data Exporter**: Export filtered audit logs with custom timestamp intervals for external auditing.

### 🔐 Authentication & Communications
- **6-Digit Cryptographic Email OTPs**: Validates user identity during registration and password resets.
- **Automated Welcome Email**: Dispatched immediately upon account verification via modern HTML template over HTTPS Port 443.
- **Profile Customizer (`/profile`)**: Users can update their username, customize default currency symbol (₹, $, €, £), and securely change passwords.
- **Root Admin Portal (`/admin`)**: Dedicated dashboard for `tabrasali7@gmail.com` with user moderation, platform volume counters, and audit logs.

---

## 🔌 REST API Endpoints

FinTrack exposes a headless RESTful API blueprint (`/api/v1/`) with CSRF exemptions for mobile applications and programmatic consumers:

| Method | Endpoint | Description | Authentication |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` or `/api/health` | Public root health check & database ping | Public |
| `GET` | `/api/v1/health` | System diagnostics & MySQL heartbeat | Public |
| `GET` | `/api/v1/summary` | Monthly financial aggregations & account balances | Session Required |
| `GET` | `/api/v1/transactions` | Paginated transaction history with filters | Session Required |
| `GET` | `/api/v1/categories` | User-defined category catalog & icons | Session Required |

---

## 🛡️ Security & Defensive Engineering

1. **CSRF Protection**: All mutating operations enforce cryptographic token verification via `Flask-WTF`.
2. **IDOR Defense**: All database queries strictly scope operations to `current_user.id`, preventing cross-tenant access.
3. **Port 443 Email API Bypassing**: Transports transactional emails over HTTPS REST endpoints to circumvent cloud SMTP firewall restrictions (e.g. Render blocking ports 25, 465, and 587).
4. **Brute-Force Rate Limiting**: Powered by `Flask-Limiter` with strict caps on `/login`, `/register`, and `/verify-otp`.
5. **Self-Healing Schema Migrations**: Inspects and synchronizes missing tables and columns on boot without downtime.

---

## 🛠️ Technology Stack

```mermaid
graph TD
    Client["Modern Web & Mobile Browsers"] -->|HTTPS / Port 443| Render["Render Cloud Web Service (Gunicorn WSGI)"]
    Render --> FlaskApp["Flask Application Factory (Python 3.14)"]
    FlaskApp --> SQLAlchemy["SQLAlchemy 2.0 ORM Engine"]
    SQLAlchemy --> CleverCloud["Clever Cloud MySQL 8.0 Database (TLS)"]
    FlaskApp --> BrevoAPI["Brevo / Resend HTTPS Email API (Port 443)"]
    FlaskApp --> ChartJS["Chart.js Hardware Accelerated Visuals"]
```

- **Backend**: Python 3.14, Flask, SQLAlchemy 2.0, Flask-Login, Flask-WTF, Flask-Limiter, Werkzeug
- **Database**: MySQL 8.0 Cloud Instance (Clever Cloud, utf8mb4 collation)
- **Frontend**: Jinja2, HTML5 Semantic Markup, Vanilla CSS3 (Custom Dark Theme), Chart.js
- **DevOps**: Docker, Docker Compose, GitHub Actions CI, Render Auto-Deploy
- **Testing**: Pytest (23/23 unit and integration tests passing)

---

## ⚙️ Local Development & Setup

### Prerequisites
- Python 3.11+ (or Python 3.14)
- MySQL Server (or Docker)

### Option 1: Docker (Fastest)
```bash
docker compose up --build
```
Navigate to `http://localhost:5000`.

---

### Option 2: Local Python Environment

1. **Clone Repository:**
   ```bash
   git clone https://github.com/md-rounaq-ali/personal-finance-tracker.git
   cd personal-finance-tracker
   ```

2. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux / macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure `.env` File:**
   ```env
   FLASK_APP=run.py
   SECRET_KEY=generate-a-strong-random-key-here
   DATABASE_URL=mysql+pymysql://root:password@localhost:3306/personal_finance_tracker?charset=utf8mb4
   
   # Optional: Email Service (Brevo HTTP or Gmail SMTP)
   BREVO_API_KEY=your_xkeysib_api_key
   MAIL_USERNAME=fintrack.security@gmail.com
   ```

5. **Start Development Server:**
   ```bash
   python run.py
   ```

---

## 🧪 Automated Testing

FinTrack features complete test coverage for models, accounting invariants, IDOR rules, API endpoints, and SEO sitemaps:

```bash
pytest tests/ -v
```

```text
tests/test_admin.py::test_admin_panel_forbidden_for_regular_user PASSED
tests/test_admin.py::test_admin_panel_accessible_for_tabrasali7 PASSED
tests/test_admin.py::test_admin_can_delete_regular_user PASSED
tests/test_api.py::test_api_health PASSED
tests/test_api.py::test_api_summary_requires_auth PASSED
tests/test_api.py::test_api_summary_authenticated PASSED
tests/test_auth.py::test_register_and_verify_otp_flow PASSED
tests/test_auth.py::test_register_duplicate_email PASSED
tests/test_auth.py::test_update_profile_username PASSED
tests/test_auth.py::test_forgot_and_reset_password_flow PASSED
tests/test_auth.py::test_login_and_logout PASSED
tests/test_auth.py::test_unauthorized_access PASSED
tests/test_landing_and_seo.py::test_landing_page_unauthenticated PASSED
tests/test_landing_and_seo.py::test_landing_page_authenticated_redirects PASSED
tests/test_landing_and_seo.py::test_robots_txt PASSED
tests/test_landing_and_seo.py::test_sitemap_xml PASSED
tests/test_landing_and_seo.py::test_health_endpoints PASSED
tests/test_models.py::test_password_hashing PASSED
tests/test_models.py::test_user_creation PASSED
tests/test_models.py::test_account_and_balance_precision PASSED
tests/test_transactions.py::test_add_expense_updates_balance PASSED
tests/test_transactions.py::test_idor_protection_on_foreign_account PASSED
tests/test_transactions.py::test_account_to_account_transfer PASSED

============================= 23 passed in 4.5s ==============================
```

---

## 👨‍💻 Author & Attribution

- **Developer**: **[Md Rounaq Ali](https://md-rounaq-ali.netlify.app/)**
- **Portfolio**: [https://md-rounaq-ali.netlify.app/](https://md-rounaq-ali.netlify.app/)
- **Google Search**: [md rounaq ali](https://www.google.com/search?q=md+rounaq+ali)
- **GitHub**: [@md-rounaq-ali](https://github.com/md-rounaq-ali)

---

## 📄 License
This project is open-source and released under the [MIT License](LICENSE).
<br />
© 2026 NexBrief. All rights reserved. Developed by [Md Rounaq Ali](https://md-rounaq-ali.netlify.app/).
