import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)

from app import app, init_db_schema
from extensions import db
from models import User, Expense, Income, Budget, Goal, GoalPart, Investment, Account, FinancialAlert
from services.spending_analysis import (
    get_spending_analysis,
    get_monthly_spending_trend,
    get_advanced_spending_patterns,
    get_rebuilt_analytics_data,
    get_goal_expense_analytics
)
from services.alert_service import check_and_create_alerts, get_user_alerts

def run_comprehensive_presentation_verification():
    print("============================================================")
    print("RUNNING COMPREHENSIVE PRESENTATION DATASET VERIFICATION")
    print("============================================================")

    client = app.test_client()

    with app.app_context():
        init_db_schema()

        # 1. LOGIN VERIFICATION
        vicky_email = "vicky@gmail.com"
        user = User.query.filter_by(email=vicky_email).first()
        assert user is not None, "User vicky@gmail.com does not exist!"

        login_res = client.post("/login", data={
            "email": vicky_email,
            "password": "Vicky@123"
        }, follow_redirects=True)
        assert login_res.status_code == 200, f"Login HTTP status {login_res.status_code}"
        print("[CHECK 1: LOGIN] PASS (Logged in as vicky@gmail.com)")

        uid = user.id

        # 2. DASHBOARD ACCESS
        dash_res = client.get("/dashboard")
        assert dash_res.status_code == 200, f"Dashboard HTTP status {dash_res.status_code}"
        dash_html = dash_res.data.decode("utf-8")
        print("[CHECK 2: DASHBOARD ACCESS] PASS (Loaded dashboard successfully)")

        # 3, 4, 5. FINANCIAL SUMMARY (INCOME, EXPENSE, SAVINGS)
        incomes = Income.query.filter_by(user_id=uid).all()
        expenses = Expense.query.filter_by(user_id=uid).all()
        
        tot_inc = sum(i.amount for i in incomes)
        tot_exp = sum(e.amount for e in expenses)
        tot_sav = tot_inc - tot_exp

        print(f"  - Total Income: ₹{tot_inc:,.2f} (Target: ₹30,000)")
        print(f"  - Total Expenses: ₹{tot_exp:,.2f} (Target: ₹22,750)")
        print(f"  - Net Savings: ₹{tot_sav:,.2f} (Target: ₹7,250)")

        assert tot_inc == 30000.0, f"Expected total income 30000, got {tot_inc}"
        assert tot_exp == 22750.0, f"Expected total expenses 22750, got {tot_exp}"
        assert tot_sav == 7250.0, f"Expected net savings 7250, got {tot_sav}"
        print("[CHECK 3, 4, 5: FINANCIAL SUMMARY] PASS")

        # 6, 7. BUDGET USAGE (~70%, BELOW 100%)
        budget_obj = Budget.query.filter_by(user_id=uid).first()
        assert budget_obj is not None, "Budget object not found"
        budget_limit = budget_obj.monthly_budget
        rem_budget = budget_limit - tot_exp
        budget_pct = round((tot_exp / budget_limit) * 100, 1)

        print(f"  - Budget Limit: ₹{budget_limit:,.2f}")
        print(f"  - Amount Spent: ₹{tot_exp:,.2f}")
        print(f"  - Remaining Budget: ₹{rem_budget:,.2f}")
        print(f"  - Budget Used: {budget_pct}%")

        assert budget_limit == 32500.0, f"Expected budget limit 32500, got {budget_limit}"
        assert rem_budget == 9750.0, f"Expected remaining budget 9750, got {rem_budget}"
        assert budget_pct == 70.0, f"Expected budget usage 70.0%, got {budget_pct}%"
        assert budget_pct < 100.0, "Budget usage is over 100%!"
        print("[CHECK 6, 7: BUDGET USAGE] PASS (~70%, Below 100%)")

        # 8. EXPENSES CONNECTED TO ACCOUNTS
        for e in expenses:
            assert e.account_id is not None, f"Expense {e.title} is missing account_id"
            assert e.account is not None, f"Expense {e.title} missing account relationship"
        print("[CHECK 8: EXPENSES CONNECTED TO ACCOUNTS] PASS")

        # 9, 10. GOAL-EXPENSE CONNECTION & VISIBILITY
        linked_exp_count = sum(1 for e in expenses if e.goal_id is not None)
        assert linked_exp_count >= 1, "No expense linked to a financial goal!"

        goal_analytics = get_goal_expense_analytics(uid)
        assert goal_analytics["goals_with_expenses_count"] >= 1, "Goal analytics does not recognize linked expenses"
        assert goal_analytics["total_all_goal_linked"] > 0, "Goal-linked expense total is 0"
        print(f"  - Linked Expenses Count: {linked_exp_count}")
        print(f"  - Total Goal-linked Spending: ₹{goal_analytics['total_all_goal_linked']:,.2f}")
        print("[CHECK 9, 10: GOAL-EXPENSE CONNECTION] PASS")

        # 11. BUDGET INFORMATION & PAGES
        budgets_page = client.get("/budgets").data.decode("utf-8")
        assert "32,500" in budgets_page or "32500" in budgets_page, "Budgets page missing budget limit"
        print("[CHECK 11: BUDGET INFORMATION] PASS")

        # 12. INVESTMENTS
        investments = Investment.query.filter_by(user_id=uid).all()
        assert len(investments) in [2, 3], f"Expected 2 or 3 investments, got {len(investments)}"
        tot_inv_amt = sum(inv.invested_amount for inv in investments)
        tot_curr_val = sum(inv.current_value for inv in investments)
        print(f"  - Total Invested Amount: ₹{tot_inv_amt:,.2f}")
        print(f"  - Portfolio Current Value: ₹{tot_curr_val:,.2f}")

        inv_page = client.get("/investments").data.decode("utf-8")
        assert "Nifty 50 Index Fund" in inv_page, "Investments page missing Nifty 50 Index Fund"
        print("[CHECK 12: INVESTMENTS] PASS")

        # 13, 14. ANALYTICS & CHARTS
        analytics_page = client.get("/analytics").data.decode("utf-8")
        assert "Analytics" in analytics_page, "Analytics page failed to load"
        
        spending_analysis = get_spending_analysis(uid)
        assert spending_analysis["highest_spending_category"] == "Food", f"Expected top category Food, got {spending_analysis['highest_spending_category']}"
        print(f"  - Top Spending Category: {spending_analysis['highest_spending_category']} (₹{spending_analysis['highest_spending_amount']:,.2f})")
        print("[CHECK 13, 14: ANALYTICS & CHARTS] PASS")

        # 15, 16. ALERTS & DEDUPLICATION
        check_and_create_alerts(uid)
        unread_alerts = get_user_alerts(uid, include_read=False)
        print(f"  - Active Unread Alerts Count: {len(unread_alerts)}")
        for a in unread_alerts:
            print(f"    * [{a.severity}] {a.title}: {a.message}")

        # Check no Budget Exceeded alert exists
        budget_exceeded_alerts = [a for a in unread_alerts if "Exceeded" in a.title]
        assert len(budget_exceeded_alerts) == 0, "Budget Exceeded alert should NOT exist when budget is 70%!"

        # Check deduplication on re-check
        check_and_create_alerts(uid)
        unread_after_recheck = get_user_alerts(uid, include_read=False)
        assert len(unread_after_recheck) == len(unread_alerts), "Duplicate alerts generated on re-check!"
        print("[CHECK 15, 16: ALERTS & DEDUPLICATION] PASS")

        # 17, 18. ROUTE HEALTH & REGRESSION TESTING
        routes_to_test = [
            "/dashboard",
            "/expenses",
            "/income",
            "/accounts",
            "/budgets",
            "/goals",
            "/investments",
            "/analytics",
            "/profile"
        ]
        for route in routes_to_test:
            res = client.get(route)
            assert res.status_code == 200, f"Route {route} returned status {res.status_code}"
        print("[CHECK 17, 18: CORE ROUTES REGRESSION HEALTH] PASS (All routes returned HTTP 200)")

    print("\n============================================================")
    print("ALL 18 PRESENTATION DATASET CHECKS PASSED PERFECTLY!")
    print("============================================================")

if __name__ == "__main__":
    run_comprehensive_presentation_verification()
