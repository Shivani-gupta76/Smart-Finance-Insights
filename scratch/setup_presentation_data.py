import os
import sys
from datetime import date, datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)

from app import app, init_db_schema
from extensions import db
from models import User, Expense, Income, Budget, Goal, GoalPart, Investment, Account, FinancialAlert
from services.spending_analysis import get_spending_analysis, get_monthly_spending_trend
from services.alert_service import check_and_create_alerts, get_user_alerts

def setup_presentation_data():
    print("============================================================")
    print("SETTING UP PRESENTATION DATASET FOR vicky@gmail.com")
    print("============================================================")

    with app.app_context():
        init_db_schema()

        # 1. Find Vicky user account
        user = User.query.filter_by(email="vicky@gmail.com").first()
        assert user is not None, "User vicky@gmail.com must exist!"
        uid = user.id

        print(f"Target User: {user.full_name} ({user.email}) [ID: {uid}]")

        # 2. Inspect existing records to be removed
        old_expenses = Expense.query.filter_by(user_id=uid).all()
        old_incomes = Income.query.filter_by(user_id=uid).all()
        old_budgets = Budget.query.filter_by(user_id=uid).all()
        old_investments = Investment.query.filter_by(user_id=uid).all()
        old_goals = Goal.query.filter_by(user_id=uid).all()
        old_accounts = Account.query.filter_by(user_id=uid).all()
        old_alerts = FinancialAlert.query.filter_by(user_id=uid).all()

        print(f"\n--- EXISTING RECORDS TO BE REMOVED FOR VICKY ---")
        print(f"  - Old Expenses: {len(old_expenses)}")
        print(f"  - Old Incomes: {len(old_incomes)}")
        print(f"  - Old Budgets: {len(old_budgets)}")
        print(f"  - Old Investments: {len(old_investments)}")
        print(f"  - Old Goals: {len(old_goals)}")
        print(f"  - Old Accounts: {len(old_accounts)}")
        print(f"  - Old Alerts: {len(old_alerts)}")

        # Clean up Vicky's old records
        # First remove budgets linked to goals
        for b in old_budgets:
            b.goal_id = None
        db.session.commit()

        for exp in old_expenses:
            db.session.delete(exp)
        for inc in old_incomes:
            db.session.delete(inc)
        for b in old_budgets:
            db.session.delete(b)
        for inv in old_investments:
            db.session.delete(inv)
        for g in old_goals:
            db.session.delete(g)
        for acc in old_accounts:
            db.session.delete(acc)
        for alt in old_alerts:
            db.session.delete(alt)

        db.session.commit()
        print("  -> Old records removed successfully.")

        # 3. Create Presentation Account
        # Initial Balance: ₹50,000
        account = Account(
            account_name="Presentation Savings Account",
            account_type="Savings",
            balance=50000.0,
            description="Primary presentation savings account",
            user_id=uid
        )
        db.session.add(account)
        db.session.commit()
        print(f"\n--- CREATED PRESENTATION ACCOUNT ---")
        print(f"  - Account Name: {account.account_name}, Initial Balance: ₹{account.balance:,.2f}")

        # 4. Create Presentation Income
        # Amount: ₹20,000, Source: Monthly Salary
        income = Income(
            title="Monthly Salary",
            source="Monthly Salary",
            amount=20000.0,
            income_date=date.today(),
            description="Primary monthly salary",
            user_id=uid
        )
        db.session.add(income)
        # Update account balance for income
        account.balance += income.amount
        db.session.commit()
        print(f"\n--- CREATED PRESENTATION INCOME ---")
        print(f"  - Source: {income.source}, Amount: ₹{income.amount:,.2f}")
        print(f"  - Updated Account Balance: ₹{account.balance:,.2f}")

        # 5. Create Presentation Expenses
        # Food: ₹3,000, Transport: ₹1,500, Shopping: ₹2,000, Entertainment: ₹1,000 -> Total ₹7,500
        expense_data = [
            {"title": "Food & Dining", "category": "Food", "amount": 3000.0},
            {"title": "Commute & Transport", "category": "Transport", "amount": 1500.0},
            {"title": "Clothes & Shopping", "category": "Shopping", "amount": 2000.0},
            {"title": "Movies & Entertainment", "category": "Entertainment", "amount": 1000.0}
        ]

        total_exp_sum = 0.0
        for item in expense_data:
            exp = Expense(
                title=item["title"],
                category=item["category"],
                amount=item["amount"],
                payment_method="Card",
                account_id=account.id,
                expense_date=date.today(),
                description=f"Presentation expense for {item['category']}",
                user_id=uid
            )
            db.session.add(exp)
            account.balance -= item["amount"]
            total_exp_sum += item["amount"]

        db.session.commit()
        print(f"\n--- CREATED PRESENTATION EXPENSES ---")
        print(f"  - Expenses count: {len(expense_data)}, Total: ₹{total_exp_sum:,.2f}")
        print(f"  - Final Account Balance (₹50,000 + ₹20,000 - ₹7,500): ₹{account.balance:,.2f}")

        # 6. Create Presentation Goal
        # Buy a Laptop, Short Term, Target: ₹1,00,000, Current: ₹25,000, Priority: High, Status: In Progress
        goal = Goal(
            goal_name="Buy a Laptop",
            goal_type="Short Term",
            target_amount=100000.0,
            current_amount=25000.0,
            target_date=date(2026, 12, 31),
            category="Electronics",
            priority="High",
            status="In Progress",
            notes="Savings for presentation laptop",
            user_id=uid
        )
        db.session.add(goal)
        db.session.commit()
        print(f"\n--- CREATED PRESENTATION GOAL ---")
        print(f"  - Goal Name: {goal.goal_name}, Target: ₹{goal.target_amount:,.2f}, Saved: ₹{goal.current_amount:,.2f}")

        # 7. Create Goal Parts
        part1 = GoalPart(
            goal_id=goal.id,
            part_name="Laptop Purchase Research",
            step_order=1,
            estimated_cost=0.0,
            actual_cost=0.0,
            status="Completed",
            notes="Compare specifications and pricing"
        )
        part2 = GoalPart(
            goal_id=goal.id,
            part_name="Savings",
            step_order=2,
            estimated_cost=25000.0,
            actual_cost=25000.0,
            status="Completed",
            notes="Initial deposit saved"
        )
        part3 = GoalPart(
            goal_id=goal.id,
            part_name="Final Purchase",
            step_order=3,
            estimated_cost=75000.0,
            actual_cost=0.0,
            status="Pending",
            notes="Remaining balance to save"
        )
        db.session.add_all([part1, part2, part3])
        db.session.commit()
        print(f"  - Created 3 Goal Parts for '{goal.goal_name}'")

        # 8. Create Presentation Budget & Link to Goal
        # Monthly Budget: ₹10,000
        budget = Budget(
            monthly_budget=10000.0,
            month="August",
            year=2026,
            user_id=uid,
            goal_id=goal.id
        )
        db.session.add(budget)
        db.session.commit()
        print(f"\n--- CREATED PRESENTATION BUDGET ---")
        print(f"  - Monthly Budget: ₹{budget.monthly_budget:,.2f}, Linked Goal: {goal.goal_name}")

        # 9. Create Presentation Investment
        # Nifty 50 Index Fund, Mutual Fund, Quantity: 10, Invested: ₹10,000, Current: ₹11,500
        investment = Investment(
            instrument_name="Nifty 50 Index Fund",
            asset_type="Mutual Fund",
            quantity=10.0,
            invested_amount=10000.0,
            current_value=11500.0,
            purchase_date=date(2026, 1, 15),
            description="Presentation index fund investment",
            user_id=uid
        )
        db.session.add(investment)
        db.session.commit()
        print(f"\n--- CREATED PRESENTATION INVESTMENT ---")
        inv_return = investment.current_value - investment.invested_amount
        inv_ret_pct = (inv_return / investment.invested_amount) * 100
        print(f"  - Instrument: {investment.instrument_name}, Invested: ₹{investment.invested_amount:,.2f}, Current: ₹{investment.current_value:,.2f}, Return: ₹{inv_return:,.2f} ({inv_ret_pct:.1f}%)")

        # 10. Generate Financial Event Alerts
        check_and_create_alerts(uid)
        alerts = get_user_alerts(uid, include_read=False)
        print(f"\n--- GENERATED FINANCIAL ALERTS ---")
        for alt in alerts:
            print(f"  - Alert: '{alt.title}' -> {alt.message}")

    print("\n============================================================")
    print("PRESENTATION DATASET SETUP COMPLETE!")
    print("============================================================")

if __name__ == "__main__":
    setup_presentation_data()
