from flask import Flask, render_template, request, redirect, url_for, session, flash
import re
from datetime import date, timedelta
from flask_login import login_required, current_user
from sqlalchemy import func, inspect, text

from config import Config
from extensions import db, login_manager, bcrypt, csrf, limiter
from flask_wtf.csrf import CSRFError

from models import User
from models.expense import Expense
from models.budget import Budget
from models.income import Income
from models.account import Account
from models.goal import Goal
from models.alert import FinancialAlert

from services.spending_analysis import get_spending_analysis, get_monthly_spending_trend, get_goal_expense_analytics, calculate_financial_health_score
from services.alert_service import check_and_create_alerts, get_user_alerts, mark_alert_as_read

from routes.auth import auth
from routes.profile import profile
from routes.expense import expense
from routes.budget import budget
from routes.income import income
from routes.account import account
from routes.investment import investment
from routes.goal import goal
from routes.analytics import analytics_bp
from routes.alert import alert_bp
from routes.reports import reports_bp

app = Flask(__name__)

app.config.from_object(Config)

# Initialize Extensions
db.init_app(app)
login_manager.init_app(app)
bcrypt.init_app(app)
csrf.init_app(app)
limiter.init_app(app)

# Custom Security Error Handlers
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template("login.html", error=f"CSRF Validation Failed: {e.description}"), 400

@app.errorhandler(429)
def handle_ratelimit_error(e):
    return render_template("login.html", error="Too many login attempts. Please wait 1 minute before trying again."), 429

# Flask-Login Configuration
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_global_vars():
    if current_user.is_authenticated:
        unread_count = FinancialAlert.query.filter_by(user_id=current_user.id, is_read=False).count()
        recent_alerts = FinancialAlert.query.filter_by(
            user_id=current_user.id
        ).order_by(
            FinancialAlert.created_at.desc()
        ).limit(15).all()

        return dict(
            unread_alerts_count=unread_count,
            global_recent_alerts=recent_alerts
        )
    else:
        return dict(
            unread_alerts_count=0,
            global_recent_alerts=[]
        )


# Register Blueprints
app.register_blueprint(auth)
app.register_blueprint(profile)
app.register_blueprint(expense)
app.register_blueprint(budget)
app.register_blueprint(income)
app.register_blueprint(account)
app.register_blueprint(investment)
app.register_blueprint(goal)
app.register_blueprint(analytics_bp)
app.register_blueprint(alert_bp)
app.register_blueprint(reports_bp)



# Home Page
@app.route("/")
def home():
    return redirect(url_for("auth.login"))


# Safe Database Migration & Performance Indexing Helper
def init_db_schema():
    with app.app_context():
        db.create_all()
        try:
            inspector = inspect(db.engine)
            if "users" in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns("users")]
                if "profile_image" not in columns:
                    with db.engine.begin() as conn:
                        conn.execute(text("ALTER TABLE users ADD COLUMN profile_image VARCHAR(255)"))
                if "theme_preference" not in columns:
                    with db.engine.begin() as conn:
                        conn.execute(text("ALTER TABLE users ADD COLUMN theme_preference VARCHAR(20) DEFAULT 'light'"))
                else:
                    with db.engine.begin() as conn:
                        conn.execute(text("UPDATE users SET theme_preference = 'light' WHERE theme_preference = 'system' OR theme_preference IS NULL"))

            if "budgets" in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns("budgets")]
                if "goal_id" not in columns:
                    with db.engine.begin() as conn:
                        conn.execute(text("ALTER TABLE budgets ADD COLUMN goal_id INTEGER REFERENCES goals(id)"))

            if "expenses" in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns("expenses")]
                if "goal_id" not in columns:
                    with db.engine.begin() as conn:
                        conn.execute(text("ALTER TABLE expenses ADD COLUMN goal_id INTEGER REFERENCES goals(id)"))


            # Milestone 4 Performance Optimization: Add Database Indexes
            with db.engine.begin() as conn:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses (user_id, expense_date)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_expenses_goal ON expenses (goal_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_incomes_user_date ON incomes (user_id, income_date)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_budgets_user_month_year ON budgets (user_id, month, year)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_goals_user_status ON goals (user_id, status)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_goals_target_date ON goals (target_date)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_goal_parts_goal ON goal_parts (goal_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alerts_user_unread ON financial_alerts (user_id, is_read)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts (user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_investments_user ON investments (user_id)"))


        except Exception as e:
            app.logger.warning(f"Schema check warning: {e}")


# Initialize Database Schema & Performance Indexes on App Startup
init_db_schema()


# Optimized Dashboard
@app.route("/dashboard")
@login_required
def dashboard():

    # Optimized direct SQL aggregations for totals
    total_expenses = db.session.query(func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or 0.0
    total_income = db.session.query(func.sum(Income.amount)).filter_by(user_id=current_user.id).scalar() or 0.0
    total_account_balance = db.session.query(func.sum(Account.balance)).filter_by(user_id=current_user.id).scalar() or 0.0

    # Fetch recent transactions only (Limit 5)
    recent_transactions = (
        Expense.query
        .filter_by(user_id=current_user.id)
        .order_by(Expense.expense_date.desc(), Expense.id.desc())
        .limit(5)
        .all()
    )

    # Get user's budget for current month & current year, accounts, and goals
    today = date.today()
    curr_month_name = today.strftime("%B")
    curr_year = today.year

    budget_obj = Budget.query.filter(
        Budget.user_id == current_user.id,
        func.lower(Budget.month) == curr_month_name.lower(),
        Budget.year == curr_year
    ).first()

    goals = Goal.query.filter_by(user_id=current_user.id).all()

    # Net Savings & Budget Metrics for Lower Dashboard Cards (All-Time Totals preserved)
    total_savings = total_income - total_expenses
    budget_amount = budget_obj.monthly_budget if budget_obj else 0.0

    # Current-Month Calculations for Hero Section (Bounded to current month through today)
    start_date = date(curr_year, today.month, 1)
    if today.month == 12:
        last_day_curr = date(curr_year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day_curr = date(curr_year, today.month + 1, 1) - timedelta(days=1)
    end_date = min(today, last_day_curr)

    current_month_income = db.session.query(func.sum(Income.amount)).filter(
        Income.user_id == current_user.id,
        Income.income_date >= start_date,
        Income.income_date <= end_date
    ).scalar() or 0.0

    current_month_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).scalar() or 0.0

    monthly_savings = current_month_income - current_month_expenses
    remaining_budget = budget_amount - current_month_expenses if budget_amount > 0 else 0.0
    budget_used = round((current_month_expenses / budget_amount) * 100, 1) if budget_amount > 0 else 0.0

    # Expense Breakdown (Pie Chart) via SQL aggregation
    category_data = (
        db.session.query(
            Expense.category,
            func.sum(Expense.amount)
        )
        .filter(Expense.user_id == current_user.id)
        .group_by(Expense.category)
        .all()
    )

    categories = [item[0] for item in category_data]
    amounts = [float(item[1]) for item in category_data]

    # Monthly Expense Trend (Bar Chart) via SQL aggregation
    monthly_data = (
        db.session.query(
            func.strftime("%m", Expense.expense_date),
            func.sum(Expense.amount)
        )
        .filter(Expense.user_id == current_user.id)
        .group_by(func.strftime("%m", Expense.expense_date))
        .all()
    )

    month_names = {
        "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
        "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
    }

    months = []
    monthly_amounts = []

    for month_str, amount in monthly_data:
        months.append(month_names.get(month_str, month_str))
        monthly_amounts.append(float(amount))

    # =========================================================
    # MILESTONE 3: SMART FINANCIAL INSIGHTS & SERVICES
    # =========================================================

    spending_analysis = get_spending_analysis(current_user.id)
    spending_trend = get_monthly_spending_trend(current_user.id, num_months=6)

    check_and_create_alerts(current_user.id)


    # 3. Financial Event Alerts Evaluation
    check_and_create_alerts(current_user.id)

    # 4. Expense-to-Goal Relationship Analytics

    goal_expense_analytics = get_goal_expense_analytics(current_user.id)

    return render_template(
        "dashboard.html",
        user=current_user,
        total_income=total_income,
        total_expenses=total_expenses,
        total_savings=total_savings,
        monthly_savings=monthly_savings,
        total_account_balance=total_account_balance,
        budget_amount=budget_amount,
        remaining_budget=remaining_budget,
        budget_used=budget_used,
        categories=categories,
        amounts=amounts,
        months=months,
        monthly_amounts=monthly_amounts,
        recent_transactions=recent_transactions,
        budget=budget_obj,
        goals=goals,
        spending_analysis=spending_analysis,
        spending_trend=spending_trend,
        goal_expense_analytics=goal_expense_analytics
    )


@app.route("/alerts/<int:alert_id>/read", methods=["POST"])
@login_required
def mark_alert_read(alert_id):
    mark_alert_as_read(alert_id, current_user.id)
    flash("Alert marked as read.", "success")
    return redirect(request.referrer or url_for("dashboard"))


if __name__ == "__main__":
    init_db_schema()
    app.run(debug=True)
