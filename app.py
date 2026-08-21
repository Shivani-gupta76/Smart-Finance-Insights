from flask import Flask, render_template, request, redirect, url_for, session, flash
import re
from flask_login import login_required, current_user
from sqlalchemy import func, inspect, text

from config import Config
from extensions import db, login_manager, bcrypt

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

app = Flask(__name__)

app.config.from_object(Config)

# Initialize Extensions
db.init_app(app)
login_manager.init_app(app)
bcrypt.init_app(app)

# Flask-Login Configuration
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_global_vars():
    if current_user.is_authenticated:
        unread_count = FinancialAlert.query.filter_by(user_id=current_user.id, is_read=False).count()
        return dict(unread_alerts_count=unread_count)
    return dict(unread_alerts_count=0)


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


# Home Page
@app.route("/")
def home():
    return redirect(url_for("auth.login"))


# Safe Database Migration Helper
def init_db_schema():
    with app.app_context():
        db.create_all()
        try:
            inspector = inspect(db.engine)
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
        except Exception as e:
            app.logger.warning(f"Schema check warning: {e}")


# Dashboard
@app.route("/dashboard")
@login_required
def dashboard():

    # Get all expenses (latest first)
    expenses = (
        Expense.query
        .filter_by(user_id=current_user.id)
        .order_by(
            Expense.expense_date.desc(),
            Expense.id.desc()
        )
        .all()
    )

    # Latest 5 transactions
    recent_transactions = expenses[:5]

    # Get all incomes
    incomes = Income.query.filter_by(user_id=current_user.id).all()

    # Get user's budget
    budget_obj = Budget.query.filter_by(user_id=current_user.id).first()

    # Get user's accounts
    accounts = Account.query.filter_by(user_id=current_user.id).all()

    # Get user's goals
    goals = Goal.query.filter_by(user_id=current_user.id).all()

    # Calculate totals
    total_expenses = sum(exp.amount for exp in expenses)
    total_income = sum(inc.amount for inc in incomes)
    total_account_balance = sum(acc.balance for acc in accounts)

    # Savings
    total_savings = total_income - total_expenses

    # Budget amount
    budget_amount = budget_obj.monthly_budget if budget_obj else 0

    # Remaining budget
    remaining_budget = budget_amount - total_expenses

    # Budget usage percentage
    if budget_amount > 0:
        budget_used = round((total_expenses / budget_amount) * 100, 2)
    else:
        budget_used = 0

    # Expense Breakdown (Pie Chart)
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

    # Monthly Expense Trend (Bar Chart - original)
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

    # 1. Spending Pattern Analysis
    spending_analysis = get_spending_analysis(current_user.id)

    # 2. 6-Month Income vs Expense vs Savings Trend
    spending_trend = get_monthly_spending_trend(current_user.id, num_months=6)

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
