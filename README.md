# Smart Finance Insights (FinSight)

### Finance Analytics Platform for Financial Reporting and Budget Tracking

FinSight is a web-based financial analytics platform designed to help users manage personal finances, track income and expenses, plan budgets, monitor financial goals, analyze spending behavior, generate reports, and receive actionable financial insights from their financial data.

---

## 1. Project Overview

Managing personal finances effectively requires clear visibility into cash flow, budget limits, goal progress, and spending habits. FinSight addresses the challenges of fragmented financial tracking by consolidating accounts, income streams, daily expenses, monthly budgets, financial goals, and investments into a single unified analytics dashboard.

FinSight transforms raw transaction records into structured financial intelligence through automated category breakdowns, monthly spending trend analyses, rule-based budget recommendations, dynamic financial health scoring, and exportable financial reports (PDF, Word, Excel).

---

## 2. Key Features

### Financial Management
- **Income Tracking**: Log multiple income sources (Salary, Freelancing, Business, Investments, Bonus, Other) with dates and descriptions.
- **Expense Tracking**: Record detailed expenses with category tagging, payment methods (Cash, UPI, Credit Card, Debit Card, Net Banking), dates, linked accounts, and linked financial goals.
- **Account Management**: Manage multiple financial accounts (Bank, Cash, Credit Card, UPI / Wallet, Investment, Other) with real-time balance calculations.
- **Investment Tracking**: Track investment assets across Equity, Mutual Funds, Debt, Gold, Cash, and Other asset types with invested vs. current value comparison.

### Budget Management
- **Monthly Budgets**: Set target spending limits per month and year.
- **Budget Utilization**: Real-time percentage tracking of budget consumption.
- **Remaining Budget**: Dynamic calculation of remaining available funds.
- **Status Indicators**: Visual warnings when spending approaches or exceeds budget limits.
- **Budget-to-Goal Relationship**: Link monthly budgets directly to financial goals.

### Financial Goals
- **Goal Management**: Create short-term, medium-term, and long-term financial goals with target amounts, target completion dates, categories, and priorities.
- **Progress Tracking**: Track current savings against target goals with progress percentage bars and remaining balances.
- **Goal Sub-Parts**: Break complex goals down into ordered sub-steps with estimated vs. actual costs and completion statuses.
- **Goal-Linked Expenses**: Associate specific expenses with goals for targeted tracking.

### Financial Analytics
- **Spending Analysis**: Category-wise expense distribution and identification of highest-spending categories.
- **Monthly Spending Trends**: Historical monthly expense aggregations and month-over-month (MoM) comparison.
- **Cash Flow Analysis**: Real-time evaluation of total income vs. total expenses vs. net savings.
- **Financial Health Score**: Dynamic 100-point score evaluating overall financial wellness.
- **Budget Utilization Analysis**: Visual indicators of budget health and over-budget risk.
- **Goal Progress Analytics**: Overall goal completion rates and linked expense summaries.

### Intelligent Insights
- **Rule-Based Financial Insights**: Automated analysis of high budget utilization, category concentration, and spending anomalies.
- **Spending Pattern Insights**: Identification of non-essential spending trends.
- **Financial Health Evaluation**: Dynamic score breakdown across five core financial pillars.
- **Alert-Driven Risk Indicators**: Automatic notification triggers for budget overflow and overspending risks.

### Alerts & Notifications
- **Automated Alerts**: System-generated alerts for budget overflow, high category spending, and financial risks.
- **Severity Levels**: Categorized notification severity (Danger, Warning, Success, Info).
- **Notification Drawer**: Right-side slide-over drawer and top header notification bell with live unread badge counters.
- **Alert Controls**: Date range filtering, unread status filtering, and mark-as-read toggles.

### Financial Reports
- **PDF Reports**: Professional downloadable PDF financial statements formatted using ReportLab.
- **Word/DOCX Reports**: Structured Word documents generated via `python-docx`.
- **Excel/XLSX Reports**: Detailed spreadsheets with income, expense, budget, and goal sheets generated via `openpyxl`.
- **Monthly Financial Reports**: Detailed summary of monthly cash flow and category allocations.
- **Goal Progress Reports**: Dedicated reports tracking financial goals, sub-parts, and linked expenses.

### User & Security
- **Authentication**: Secure user registration, password hashing (`Flask-Bcrypt`), login, and session management (`Flask-Login`).
- **CSRF Token Protection**: Explicit cross-site request forgery protection across all forms and AJAX endpoints via `Flask-WTF`.
- **Login Rate Limiting**: Protection against brute-force attacks with IP-based rate limiting (5 attempts/min) via `Flask-Limiter`.
- **Data Isolation**: Strict user-level data segregation preventing cross-user data leakage.
- **Input Validation**: Server-side validation for dates, positive numerical amounts, and malformed inputs.

---

## 3. How FinSight Works

```
                     ┌──────────────────────────────────────────┐
                     │                User Input                │
                     │ (Income, Expenses, Accounts, Budgets,    │
                     │             Goals, Investments)          │
                     └────────────────────┬─────────────────────┘
                                          │
                                          ▼
                     ┌──────────────────────────────────────────┐
                     │        Financial Data Processing         │
                     │    (Aggregation, Account Balances,       │
                     │          Category Classification)        │
                     └────────────────────┬─────────────────────┘
                                          │
                                          ▼
                     ┌──────────────────────────────────────────┐
                     │       Spending & Budget Analysis         │
                     │ (Budget Utilization, Monthly Trends,     │
                     │        Goal Progress Calculation)        │
                     └────────────────────┬─────────────────────┘
                                          │
                                          ▼
                     ┌──────────────────────────────────────────┐
                     │       Financial Health Evaluation        │
                     │  (100-Point Dynamic Health Scoring,      │
                     │     Pillar Analysis, Risk Detection)     │
                     └────────────────────┬─────────────────────┘
                                          │
                                          ▼
                     ┌──────────────────────────────────────────┐
                     │         Recommendations & Alerts         │
                     │ (Rule-Based Insights, Automated Alerts,  │
                     │         Notification Drawer Badges)      │
                     └────────────────────┬─────────────────────┘
                                          │
                                          ▼
                     ┌──────────────────────────────────────────┐
                     │        Reports & Dashboard Insights      │
                     │    (Tabler Dashboard UI, PDF/DOCX/XLSX   │
                     │           Exports, Interactive Charts)   │
                     └──────────────────────────────────────────┘
```

1. **User Input**: The user inputs financial data including accounts, income, expenses, monthly budget limits, financial goals, and investments.
2. **Financial Data Processing**: The backend validates, sanitizes, and stores transactions, updating account balances and category totals.
3. **Spending & Budget Analysis**: The analytics engine calculates category proportions, budget utilization percentages, and progress towards goals.
4. **Financial Health Evaluation**: The application computes a dynamic 100-point Financial Health Score across five core financial metrics.
5. **Recommendations & Alerts**: Rule-based logic evaluates financial risks, triggering automated alerts and actionable recommendations.
6. **Reports & Dashboard Insights**: Aggregated metrics are presented visually on a responsive SaaS dashboard and rendered into downloadable PDF, Word, and Excel reports.

---

## 4. Financial Intelligence

### Spending Analysis
Expenses are automatically categorized and aggregated to calculate total category expenditure, percentage distribution, and month-over-month variance. The system highlights top spending categories to pinpoint cost drivers.

### Budget Analysis
Budget health is evaluated by comparing monthly expense totals against configured budget thresholds. Utilization is computed as:
$$\text{Budget Utilization (\%)} = \left( \frac{\text{Total Monthly Expenses}}{\text{Monthly Budget Amount}} \right) \times 100$$

### Personalized Recommendations
FinSight generates automated rule-based recommendations by inspecting the user's financial metrics:
- **High Utilization**: Triggered when budget utilization exceeds 80%.
- **Category Over-Concentration**: Triggered when a single category accounts for more than 40% of total expenses.
- **Low Savings Rate**: Triggered when monthly savings fall below 20% of net income.

### Financial Health Score
The platform evaluates overall financial standing using a dynamic **100-Point Scoring System** distributed across five core pillars:

| Pillar | Max Score | Evaluation Focus |
| :--- | :---: | :--- |
| **Net Savings Rate** | 25 pts | Ratio of monthly savings to total net income |
| **Budget Health** | 25 pts | Adherence to monthly budget limits |
| **Goal Progress** | 20 pts | Average completion percentage across active goals |
| **Spending Pattern** | 15 pts | Category diversification and non-essential spending control |
| **Financial Risk & Alerts** | 15 pts | Frequency and severity of active financial alerts |

---

## 5. Database Architecture

FinSight uses a relational database schema managed via SQLAlchemy ORM.

```
                               ┌──────────────┐
                               │     User     │
                               └──────┬───────┘
                                      │
     ┌──────────┬──────────┬──────────┼──────────┬──────────┬──────────┐
     │          │          │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼          ▼          ▼
 ┌───────┐  ┌───────┐  ┌────────┐ ┌────────┐ ┌──────┐ ┌──────────┐ ┌───────┐
 │Profile│  │Account│  │ Income │ │Expense │ │Budget│ │Investment│ │ Alert │
 └───────┘  └───┬───┘  └────────┘ └───┬────┘ └───┬──┘ └──────────┘ └───────┘
                │                     │          │
                └──────────┬──────────┘          │
                           │                     │
                           ▼                     │
                      ┌─────────┐                │
                      │  Goal   │◄───────────────┘
                      └────┬────┘
                           │
                           ▼
                      ┌─────────┐
                      │GoalPart │
                      └─────────┘
```

### Entity Relationships
- **User**: Core entity representing registered users.
- **Profile** (1:1 with `User`): Stores user profile information, currency preferences, and theme choices.
- **Account** (1:N with `User`, 1:N with `Expense`): Represents financial accounts (Bank, Cash, Credit Card, etc.).
- **Income** (1:N with `User`): Stores income entries.
- **Expense** (1:N with `User`, N:1 with `Account`, N:1 Optional with `Goal`): Stores expense entries.
- **Budget** (1:N with `User`, N:1 Optional with `Goal`): Defines monthly spending limits.
- **Goal** (1:N with `User`, 1:N with `GoalPart`, 1:N with `Budget`, 1:N with `Expense`): Represents target financial goals.
- **GoalPart** (N:1 with `Goal`): Represents ordered sub-steps or milestones within a goal.
- **Investment** (1:N with `User`): Stores asset investments and portfolio values.
- **FinancialAlert** (1:N with `User`): Stores system-generated notifications and severity tags.

---

## 6. Technology Stack

| Layer | Technology | Function |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3 / Flask 3 | Core application routing, request handling, and business logic |
| **ORM & Database** | SQLAlchemy / Flask-SQLAlchemy / SQLite 3 | Relational database ORM, schema migration, and data persistence |
| **Frontend UI** | HTML5, CSS3, JavaScript (ES6) | Responsive Tabler-style admin dashboard, interactive controls |
| **Templating Engine** | Jinja2 | Dynamic server-side HTML rendering |
| **Authentication** | Flask-Login | User session management and route protection |
| **Password Security** | Flask-Bcrypt | Salted password hashing and verification |
| **CSRF Protection** | Flask-WTF | CSRF token generation and request validation (`CSRFProtect`) |
| **Rate Limiting** | Flask-Limiter | IP-based request rate limiting (`5 per minute`) |
| **PDF Reporting** | ReportLab | Programmatic PDF document generation |
| **Word Reporting** | python-docx | Programmatic DOCX report creation |
| **Excel Reporting** | openpyxl | Spreadsheet report creation with multi-tab formatting |
| **Data Visualization** | Chart.js | Client-side interactive pie, bar, and line charts |
| **Automated Testing** | pytest | Automated integration and security test suite |

---

## 7. Project Structure

```
M2-SFI/
├── app.py                     # Main Flask application entry point & error handlers
├── config.py                  # Application configuration & environment settings
├── extensions.py              # Shared Flask extensions (DB, Bcrypt, Login, CSRF, Limiter)
├── requirements.txt           # Project Python dependencies
├── README.md                  # Technical project documentation
│
├── database/
│   └── finance.db             # SQLite database file
│
├── models/                    # SQLAlchemy database models
│   ├── __init__.py
│   ├── user.py
│   ├── profile.py
│   ├── account.py
│   ├── income.py
│   ├── expense.py
│   ├── budget.py
│   ├── goal.py
│   ├── goal_part.py
│   ├── investment.py
│   └── alert.py
│
├── routes/                    # Modular Blueprint route handlers
│   ├── __init__.py
│   ├── auth.py
│   ├── profile.py
│   ├── account.py
│   ├── income.py
│   ├── expense.py
│   ├── budget.py
│   ├── investment.py
│   ├── goal.py
│   ├── analytics.py
│   ├── alert.py
│   └── reports.py
│
├── services/                  # Business logic & analytics engines
│   ├── alert_service.py
│   ├── report_service.py
│   └── spending_analysis.py
│
├── static/                    # Frontend static assets
│   ├── css/                   # Stylesheets & Tabler design tokens
│   │   ├── layout.css
│   │   ├── dashboard.css
│   │   ├── analytics.css
│   │   ├── expense.css
│   │   ├── income.css
│   │   ├── account.css
│   │   ├── budget.css
│   │   ├── investment.css
│   │   ├── goal.css
│   │   ├── goal_details.css
│   │   └── profile.css
│   └── js/                    # Client-side JavaScript
│       └── analytics.js
│
├── templates/                 # Jinja2 HTML templates
│   ├── layout.html
│   ├── dashboard.html
│   ├── analytics.html
│   ├── expenses.html
│   ├── edit_expense.html
│   ├── income.html
│   ├── edit_income.html
│   ├── accounts.html
│   ├── edit_account.html
│   ├── budgets.html
│   ├── investments.html
│   ├── edit_investment.html
│   ├── goals.html
│   ├── edit_goal.html
│   ├── edit_goal_part.html
│   ├── goal_details.html
│   ├── reports.html
│   ├── alerts.html
│   ├── profile.html
│   ├── login.html
│   └── register.html
│
└── tests/                    # Test suite
    └── test_milestone4.py     # Integration and security test suite
```

---

## 8. Security Implementation

FinSight implements multi-layered security practices to safeguard user data:

- **Password Hashing**: Passwords are securely hashed using `Flask-Bcrypt` before being written to the database. Plaintext passwords are never stored or logged.
- **Authentication & Route Protection**: Access to financial data routes is restricted using Flask-Login `@login_required` decorators. Unauthenticated requests are redirected to the login endpoint.
- **Session Security**: Session cookies are configured with `HTTPOnly=True` to prevent client-side script access and `SameSite=Lax` to prevent cross-site request forgery via cookies.
- **Explicit CSRF Protection**: All POST form submissions and AJAX requests enforce CSRF token verification via `Flask-WTF` (`CSRFProtect`). Invalid or missing tokens result in an HTTP 400 response.
- **Login Rate Limiting**: The `/login` endpoint is protected by `Flask-Limiter` set to **5 login attempts per minute per IP address**. Exceeding this limit returns HTTP 429 (Too Many Requests).
- **User Data Isolation**: Database queries explicitly filter records by the logged-in user's `user_id`, ensuring strict tenant isolation across all endpoints.
- **Input Validation & Sanitization**: Server-side parsing ensures positive amounts, valid date formats, and valid enum values.

---

## 9. Financial Reporting

The platform features a multi-format financial reporting module allowing users to export financial summaries:

### Export Formats
- **PDF (ReportLab)**: Generates formatted PDF documents complete with summary statistics, category breakdown tables, and health metrics.
- **Word / DOCX (`python-docx`)**: Produces editable Word documents containing executive summaries and tables.
- **Excel / XLSX (`openpyxl`)**: Generates multi-tab Excel workbooks containing raw data sheets for Income, Expenses, Budgets, and Goals.

### Supported Reports
1. **Monthly Financial Report**: Consolidates income, expense categories, budget utilization, and net savings for any selected month and year.
2. **Goal Progress Report**: Consolidates active financial goals, current savings, progress percentages, sub-parts, and linked goal expenses.

---

## 10. User Interface

The application features a modern UI inspired by the **Tabler** admin dashboard system:

- **Professional Financial SaaS Aesthetic**: Clean light background (`#f8fafc`), dark navy sidebar (`#0f172a`), royal blue primary accent (`#2563eb`), crisp borders (`1px solid var(--card-border)`), and structured metric cards.
- **Responsive Layout**: Designed for Desktop, Laptop, Tablet, and Mobile screens with responsive tables and drawer navigation.
- **Theme Support**: Seamless Light Mode and Dark Mode support driven by unified CSS variables.
- **Visual Analytics**: Interactive Chart.js pie and bar charts for category distribution and historical trends.
- **Subtle Motion**: Smooth CSS animations (150ms–350ms) for card hover elevation, page load fade-in, progress bar filling, and drawer popups. Respects `@media (prefers-reduced-motion: reduce)`.

---

## 11. Installation Guide

### Prerequisites
- Python 3.9 or higher
- Git

### Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/M-Raghavendra/Smart-Finance-Insights.git
   cd M2-SFI
   ```

2. **Create a Virtual Environment**:
   ```bash
   # Windows
   python -m venv .venv

   # macOS / Linux
   python3 -m venv .venv
   ```

3. **Activate the Virtual Environment**:
   ```bash
   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1

   # Windows (Command Prompt)
   .venv\Scripts\activate.bat

   # macOS / Linux
   source .venv/bin/activate
   ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 12. Environment Configuration

Create a `.env` file in the project root directory based on the configuration parameters below:

```env
SECRET_KEY=your-secure-random-secret-key-here
DATABASE_URL=sqlite:///database/finance.db
SESSION_COOKIE_SECURE=False
```

## 13. Running the Application

To start the Flask development server:

```bash
python app.py
```

The application will run locally at:
`http://127.0.0.1:5000/`

Upon execution, database tables and default indexes will automatically initialize if they do not exist.

---

## 🚀 Deployment

FinSight is deployed as a production Flask application using **Render** and **Gunicorn**.

### 🌐 Live Application

**Live URL:**  
https://smart-finance-insights-rbd6.onrender.com

### ⚙️ Deployment Configuration

- **Hosting Platform:** Render
- **Source Repository:** GitHub
- **Deployment Branch:** `main`
- **Web Framework:** Flask
- **Production Server:** Gunicorn
- **Build Command:**
  ```bash
  pip install -r requirements.txt

## 14. Testing

FinSight includes an automated integration and security test suite built with `pytest`.

### Running the Tests

```bash
# Windows
.venv\Scripts\python.exe -m pytest tests/test_milestone4.py -v

# macOS / Linux
pytest tests/test_milestone4.py -v
```

### Test Coverage
The automated test suite verifies 14 test cases covering:
- User registration, password hashing, and login authentication
- Unauthenticated route protection
- User data isolation across sessions
- Dynamic monthly financial report calculation
- Goal progress and linked expense aggregation
- PDF, Word (DOCX), and Excel (XLSX) report exports
- Server-side input validation for amounts and dates
- Empty state data handling (zero-record robustness)
- Financial Health Score and alert generation regression
- Explicit CSRF token protection (valid/invalid/missing tokens)
- Login rate limiting (5 attempt limit and HTTP 429 response)

---

## 15. Data Privacy & Security Note

Financial information should be treated as sensitive data. Production deployments should use secure environment configuration, HTTPS encryption, a production-grade database management system (such as PostgreSQL), and appropriate infrastructure access controls.

---

## 16. Future Enhancements

- **API/LLM Integration**: Optional AI-driven conversational assistant for natural language financial queries and advice.
- **Predictive Forecasting**: Advanced predictive models for cash flow projection and recurring bill estimation.
- **Multi-Currency Engine**: Live exchange rate integration for real-time multi-currency conversions.
- **Cloud Database Support**: Support for managed cloud PostgreSQL databases.
- **Automated Bank Feeds**: Open Banking API integration for automated transaction importing.

---

## 17. Contribution & Development

The codebase follows a modular Flask architecture:
- `models/`: SQLAlchemy data definitions.
- `routes/`: Blueprint endpoint controllers.
- `services/`: Business logic, report generators, and analytics algorithms.
- `templates/`: Jinja2 view templates.
- `static/`: Design tokens, CSS stylesheets, and JavaScript files.

---

## 18. License

This project is developed for educational, research, and portfolio demonstration purposes.
