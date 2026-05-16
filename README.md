<div align="center">
  
  # 💰 FinTrack — Premium Personal Finance Tracker

  <p align="center">
    A full-stack, enterprise-grade personal finance management application built with Python, Flask, and MySQL.
  </p>

  <!-- Badges -->
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version" />
    <img src="https://img.shields.io/badge/Flask-3.1.1-lightgrey.svg" alt="Flask Version" />
    <img src="https://img.shields.io/badge/MySQL-8.0+-orange.svg" alt="MySQL Version" />
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
  </p>

  <h3>
    <a href="#live-demo">Live Demo</a>
    <span> | </span>
    <a href="#features">Features</a>
    <span> | </span>
    <a href="#tech-stack">Tech Stack</a>
    <span> | </span>
    <a href="#installation">Installation</a>
  </h3>
</div>

<br />

## 📸 Screenshots

*(Add your screenshots here before pushing to GitHub. Recommended: Dashboard, Transactions List, and Monthly Report)*

| Dashboard Overview | Monthly Analytics |
| :---: | :---: |
| <img src="docs/dashboard.png" width="400" alt="Dashboard Screenshot placeholder" /> | <img src="docs/reports.png" width="400" alt="Reports Screenshot placeholder" /> |

<br />

## 🚀 Live Demo

**[Click here to view the Live Demo of FinTrack](#)**  
*(Replace the link above once you deploy the application to a platform like Render or PythonAnywhere).*

---

## 📖 Project Description

FinTrack is designed to provide users with complete control over their financial health. Moving beyond simple spreadsheet tracking, this application implements a fully normalized relational database to ensure data integrity while offering a stunning, premium dark-mode user interface. 

It was built focusing on **clean code architecture**, utilizing the **Flask Application Factory pattern**, secure user authentication, and advanced SQL querying for real-time financial aggregations.

---

## ✨ Features

- **📊 Real-time Dashboard**: Interactive summaries of income, expenses, net savings, and category-wise spending using Chart.js.
- **🛡️ Secure Authentication**: User registration and login flows protected by Werkzeug password hashing and Flask-Login session management.
- **💳 Multi-Account Tracking**: Manage balances across multiple entities (Bank Accounts, Credit Cards, Digital Wallets, Cash).
- **🏷️ Smart Categorization**: 14+ default categories auto-seeded for new users, with support for custom user-defined categories featuring emojis and hex color codes.
- **🎯 Budget Alerts**: Set monthly spending limits per category. Visual progress bars warn users as they approach or exceed their budgets.
- **📉 Advanced Reporting**: Generate month-over-month comparisons, identify top expenses, and calculate overall savings rates.
- **📥 CSV Data Export**: Instantly export your transaction history for external accounting or tax purposes.

---

## 🛠️ Tech Stack

### Backend
- **Core**: Python 3
- **Framework**: Flask (Application Factory, Blueprints)
- **Database**: MySQL 8.0+
- **ORM**: SQLAlchemy
- **Migrations**: Flask-Migrate (Alembic)
- **Security**: Flask-Login, Werkzeug Security, python-dotenv

### Frontend
- **Structure**: HTML5, Jinja2 Templating
- **Styling**: Vanilla CSS3 (Custom Dark-Mode Design System, CSS Variables, Glassmorphism)
- **Interactivity**: Vanilla JavaScript
- **Data Visualization**: Chart.js

---

## ⚙️ Installation & Local Setup

Follow these steps to run the project locally on your machine.

### 1. Prerequisites
- Python 3.8 or higher installed.
- MySQL Server installed and running locally.
- Git installed.

### 2. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/personal-finance-tracker.git
cd personal-finance-tracker
```

### 3. Database Configuration
Log into your MySQL server and create a new database:
```sql
CREATE DATABASE personal_finance_tracker;
```

### 4. Environment Setup
Create a virtual environment and install the required dependencies:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Environment Variables
Create a `.env` file in the root directory and add your MySQL credentials:
```env
FLASK_APP=run.py
FLASK_DEBUG=1
SECRET_KEY=your_secure_secret_key_here
DATABASE_URL=mysql+pymysql://root:YOUR_MYSQL_PASSWORD@localhost:3306/personal_finance_tracker
```

### 6. Run Database Migrations
Initialize the tables in your MySQL database:
```bash
flask db init
flask db migrate -m "Initial schema setup"
flask db upgrade
```

### 7. Start the Server
```bash
python run.py
```
The application will be available at `http://127.0.0.1:5000`.

---

## 🗄️ Database Schema (ERD)

The application uses a robust relational model designed to prevent data anomalies:

- **Users Table**: Manages authentication and preferences.
- **Categories Table**: Defines income/expense types, linked via Foreign Key to Users.
- **Accounts Table**: Tracks balances for different financial sources.
- **Transactions Table**: The core fact table linking Users, Accounts, and Categories. Ensures full auditability.
- **Budgets Table**: Manages monthly threshold limits.

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](#).

## 📄 License
This project is [MIT](https://choosealicense.com/licenses/mit/) licensed.
