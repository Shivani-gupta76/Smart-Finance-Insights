from flask import Flask, render_template, request, redirect, url_for, session
import re
from flask_login import login_required, current_user
from sqlalchemy import func

from config import Config
from extensions import db, login_manager, bcrypt

from models import User
from models.expense import Expense
from models.budget import Budget
from models.income import Income
from models.account import Account



from routes.auth import auth
from routes.profile import profile
from routes.expense import expense
from routes.budget import budget
from routes.income import income
from routes.account import account
from routes.investment import investment
from routes.goal import goal

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


# Register Blueprints
app.register_blueprint(auth)
app.register_blueprint(profile)
app.register_blueprint(expense)
app.register_blueprint(budget)
app.register_blueprint(income)
app.register_blueprint(account)
app.register_blueprint(investment)
app.register_blueprint(goal)


# Home Page
@app.route("/")
def home():
    return redirect(url_for("auth.login"))


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
    budget = Budget.query.filter_by(user_id=current_user.id).first()

    # Get user's accounts
    accounts = Account.query.filter_by(user_id=current_user.id).all()

    # Calculate totals
    total_expenses = sum(
        exp.amount for exp in expenses
    )

    total_income = sum(
        inc.amount for inc in incomes
    )

    total_account_balance = sum(
        acc.balance for acc in accounts
    )


    # Savings
    total_savings = total_income - total_expenses

    # Budget amount
    budget_amount = budget.monthly_budget if budget else 0

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

    # Monthly Expense Trend (Bar Chart)
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
        "01": "Jan",
        "02": "Feb",
        "03": "Mar",
        "04": "Apr",
        "05": "May",
        "06": "Jun",
        "07": "Jul",
        "08": "Aug",
        "09": "Sep",
        "10": "Oct",
        "11": "Nov",
        "12": "Dec"
    }

    months = []
    monthly_amounts = []

    for month, amount in monthly_data:
        months.append(month_names.get(month, month))
        monthly_amounts.append(float(amount))

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
        recent_transactions=recent_transactions
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)