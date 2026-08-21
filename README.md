# Finance Analytics Platform for Financial Reporting and Budget Tracking

## Project Overview

FinSight is a comprehensive full-stack personal financial management and analytics platform built with Flask, SQLAlchemy, SQLite, and Chart.js. The platform enables users to track income, manage multi-category expenses, monitor bank and savings account balances, build budgets, manage investment portfolios, plan multi-step financial goals, receive real-time event-driven financial alerts, and view interactive smart financial dashboards.

---

## Milestone 1 — Core Financial Management & Reporting

- **User Authentication**: Secure user registration, email format validation, password hashing (Flask-Bcrypt), login, and session-protected logout (Flask-Login).
- **User Profile**: Profile management, personal data view/update.
- **Income Management**: Record, edit, delete, and filter income entries with source categorization.
- **Expense Management**: Log, edit, and delete category-specific expenses linked to financial accounts.
- **Account Synchronization**: Multi-account management (Bank, Cash, Savings) with real-time automatic balance updates upon adding, editing, or deleting expenses.
- **Budget Tracking**: Monthly budget allocation, spent vs remaining budget calculations, and usage percentage indicators.
- **Dashboard & Reporting**: Summary cards (Total Income, Total Expenses, Total Savings, Monthly Budget), category pie chart breakdown, monthly expense bar charts, and recent transaction history.

---

## Milestone 2 — Investment Portfolio & Multi-Step Goal Planning

- **Investment Portfolio Tracking**: Track investments across instruments (Stocks, Mutual Funds, Fixed Deposits, Crypto, Gold).
- **Asset Allocation & Returns**: Automated calculations for Total Invested Amount, Current Portfolio Value, Total Returns (₹), Return Percentage (%), and Asset Type allocation breakdown.
- **Financial Goal Planning**: Create, edit, and track long-term and short-term financial goals with target amounts, current saved amounts, priority levels, categories, and target deadlines.
- **Goal Progress Analytics**: Automatic goal completion status ("In Progress" vs "Completed"), progress percentages, and remaining target amount calculations.
- **Goal Parts Breakdown**: Deconstruct complex goals into ordered sub-steps/milestones with estimated costs, actual costs, cost variances, start/completion dates, and step statuses.

---

## Milestone 3

### Milestone 3 Part 1 — Implemented & Verified

- **Budget ↔ Goal Connection**: Relate each monthly budget to a specific financial goal. Linked budget details appear on Goal cards and Goal detail headers; linked Goal details appear on Budget management forms. Deleting a Goal safely retains the Budget (`goal_id` set to NULL).
- **Spending Pattern Analysis**: Real database-driven spending analytics engine calculating total income, total expenses, net savings, category-wise spending distribution, top spending category identification, and month-over-month spending percentage change.
- **Explainable Spending Insights**: Rule-based analytics engine producing human-readable financial insights based on actual user transactions.
- **6-Month Historical Spending Trend**: 6-month historical Income vs Expense vs Net Savings comparison chart computed directly from database transaction dates.
- **Financial Event Alert System**: Automated detection of critical financial events including Budget Exceeded, High Category Spending (>40%), Significant Spending Increase (>15%), Negative Balance, and Approaching Goal Deadlines.
- **Alert Deduplication & Dismissal**: Guarantees zero alert duplication on dashboard refresh and provides interactive "Mark as Read" dismissal functionality.
- **Smart Financial Dashboard**: Unified dashboard section integrating Spending Insights, Top Categories progress bars, 6-Month Trend Chart, Budget Status, Goal Progress cards, and Financial Event Alert cards alongside existing Milestone 1 & 2 dashboard components.

### Milestone 3 Remaining / Additional Requirements

- **Personalized Budget Recommendations**: *Pending / Not Implemented in core engine*.
- **Financial Health Score Calculation**: *Pending / Not Implemented in core engine*.

---

## Technology Stack

- **Backend**: Python 3, Flask 3.0, Flask-SQLAlchemy 3.1, Flask-Login 0.6, Flask-Bcrypt 1.0, SQLAlchemy 2.0
- **Database**: SQLite (`database/finance.db`)
- **Frontend**: HTML5, Vanilla CSS3, JavaScript (ES6+), Jinja2 Templating, Chart.js, FontAwesome 6
- **Architecture**: Modular Flask Blueprints, Decoupled Service Layer, Model-View-Controller (MVC) design pattern

---

## Project Structure

```
M2-SFI/
├── app.py                      # Application entry point, DB schema initializer & Smart Dashboard route
├── config.py                   # Configuration settings & database URI
├── extensions.py               # Flask extension initializations (db, login_manager, bcrypt)
├── requirements.txt            # Project dependencies
├── database/
│   └── finance.db              # SQLite Database
├── models/
│   ├── __init__.py             # Model exports
│   ├── user.py                 # User authentication model
│   ├── profile.py              # User profile model
│   ├── account.py              # Financial account model
│   ├── income.py               # Income transaction model
│   ├── expense.py              # Expense transaction model
│   ├── budget.py               # Budget model with Goal relationship
│   ├── goal.py                 # Goal model
│   ├── goal_part.py            # Sub-goal / Part milestone model
│   ├── investment.py           # Investment portfolio model
│   └── alert.py                # Financial event alert model
├── routes/
│   ├── auth.py                 # Login, Register, Logout routes
│   ├── profile.py              # Profile management routes
│   ├── account.py              # Account CRUD routes
│   ├── income.py               # Income CRUD routes
│   ├── expense.py              # Expense CRUD routes & account balance sync
│   ├── budget.py               # Budget CRUD & Goal linking routes
│   ├── goal.py                 # Goal & Goal Parts management routes
│   └── investment.py           # Investment tracking & analytics routes
├── services/
│   ├── spending_analysis.py    # Spending analysis, 6-month trends & rule-based insights engine
│   └── alert_service.py        # Event alert detector & deduplication service
├── static/
│   ├── css/                    # Modular layout, dashboard, budget, goal & investment stylesheets
│   ├── images/
│   └── uploads/
└── templates/                  # Jinja2 HTML templates
    ├── layout.html
    ├── login.html
    ├── register.html
    ├── dashboard.html          # Smart Financial Dashboard
    ├── budgets.html            # Budget & Goal linkage form
    ├── goals.html              # Financial goals list
    ├── goal_details.html       # Goal details & Goal Parts breakdown
    ├── expenses.html
    ├── income.html
    ├── accounts.html
    ├── investments.html
    └── profile.html
```

---

## Database Schema & ORM Relationships

- **User**: Primary entity with 1-to-Many relationships to Accounts, Incomes, Expenses, Budgets, Goals, Investments, and FinancialAlerts.
- **Budget → Goal**: Foreign Key `goal_id` on `budgets` table referencing `goals.id` (Nullable). Relationship `goal = db.relationship("Goal", backref=db.backref("budgets", lazy=True))`.
- **FinancialAlert**: Stores user-specific alerts (`user_id`, `alert_type`, `title`, `message`, `severity`, `is_read`, `created_at`).
- **Goal → GoalPart**: 1-to-Many cascade relationship (`all, delete-orphan`).
- **Expense → Account**: Foreign Key `account_id` referencing `accounts.id` with balance synchronization.

---

## Security & Data Isolation

- **Authentication**: Session-based login using Flask-Login with hashed passwords stored via Flask-Bcrypt.
- **Multi-Tenant Data Isolation**: Every database query and service calculation explicitly filters by `current_user.id`.
- **CSRF & Route Protection**: Route access restricted using `@login_required` decorators across all financial endpoints.

---

## Testing & Verification Results

Comprehensive automated and browser-level tests were executed against local database `database/finance.db` using test credentials `vicky@gmail.com`:

| Module / Feature | Status | Verification Details |
| :--- | :--- | :--- |
| **User Authentication** | **PASS** | Registration, Login, Session Persistence & Logout verified cleanly. |
| **Account & Balance Sync** | **PASS** | Expense additions automatically deduct linked Account balance correctly. |
| **Income & Expenses** | **PASS** | CRUD operations verified; multi-category transactions calculated accurately. |
| **Investment Tracking** | **PASS** | Invested amount, current value, returns (₹ and %), and asset allocation verified. |
| **Goal & Goal Parts** | **PASS** | Goal progress %, step order, estimated vs actual cost variance, and timeline verified. |
| **Budget ↔ Goal Connection** | **PASS** | Goal-budget linking, UI badges, and Goal deletion non-cascade check verified. |
| **Spending Pattern Analysis** | **PASS** | Total Income, Expenses, Savings, Top Category (Food), and MoM change verified. |
| **6-Month Spending Trend** | **PASS** | 6-month historical Income, Expenses, and Savings arrays computed cleanly. |
| **Financial Event Alerts** | **PASS** | Event triggers (Over budget, High spending, Goal deadline) verified. |
| **Alert Deduplication & Dismissal**| **PASS** | Zero duplicate alerts on refresh; "Mark as Read" action verified. |
| **Smart Dashboard UI** | **PASS** | All new Smart Financial Insights widgets integrated without breaking existing UI. |
| **Personalized Recommendations**| **PENDING** | *Not implemented in current codebase*. |
| **Financial Health Score** | **PENDING** | *Not implemented in current codebase*. |
