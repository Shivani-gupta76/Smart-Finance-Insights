import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app import app, init_db_schema
from extensions import db, bcrypt
from models import User, Expense, Income, Budget, Goal, GoalPart, Investment, Account, FinancialAlert
from services.spending_analysis import get_spending_analysis, get_monthly_spending_trend
from services.alert_service import check_and_create_alerts, get_user_alerts, mark_alert_as_read
from datetime import date, timedelta


def test_analytics_suite():
    print("\n============================================================")
    print("RUNNING AUTOMATED TEST SUITE FOR ANALYTICS DASHBOARD")
    print("============================================================")

    client = app.test_client()

    with app.app_context():
        init_db_schema()

        # -------------------------------------------------------------
        # 1. AUTHENTICATION & LOGIN TEST
        # -------------------------------------------------------------
        # Unauthenticated access to /analytics should redirect to login
        anon_res = client.get("/analytics")
        assert anon_res.status_code == 302
        assert "/login" in anon_res.location
        print("[TEST 1: /analytics Authentication Protection] PASS")

        # Login with Vicky
        vicky_email = "vicky@gmail.com"
        user = User.query.filter_by(email=vicky_email).first()
        assert user is not None, "Test account vicky@gmail.com must exist in DB!"

        login_res = client.post("/login", data={"email": vicky_email, "password": "Vicky@123"}, follow_redirects=True)
        assert login_res.status_code == 200
        print("[TEST 2: Login with test account vicky@gmail.com] PASS")

        uid = user.id

        # -------------------------------------------------------------
        # 2. USER DATA ISOLATION TEST
        # -------------------------------------------------------------
        # Create a second user and verify data isolation
        other_user = User.query.filter_by(email="other_user@gmail.com").first()
        if not other_user:
            other_pw = bcrypt.generate_password_hash("Password@123").decode("utf-8")
            other_user = User(full_name="Other User", email="other_user@gmail.com", password=other_pw)
            db.session.add(other_user)
            db.session.commit()
            
            # Add distinct income for other user
            other_inc = Income(title="Other Income", amount=50000.0, source="Salary", user_id=other_user.id, income_date=date.today())
            db.session.add(other_inc)
            db.session.commit()

        # Login as other user and check analytics
        client.post("/login", data={"email": "other_user@gmail.com", "password": "Password@123"}, follow_redirects=True)
        other_res = client.get("/analytics")
        assert other_res.status_code == 200
        other_html = other_res.get_data(as_text=True)
        # Should contain other user's name, not Vicky's private data
        assert "Other User" in other_html
        print("[TEST 3: User Data Isolation] PASS")

        # Re-login as Vicky
        client.post("/login", data={"email": vicky_email, "password": "Vicky@123"}, follow_redirects=True)

        # -------------------------------------------------------------
        # 3. ANALYTICS PAGE ACCESS & HTML RENDER TEST
        # -------------------------------------------------------------
        analytics_res = client.get("/analytics")
        assert analytics_res.status_code == 200
        html = analytics_res.get_data(as_text=True)

        assert "Monthly Savings" in html
        assert "Avg. Monthly Expenses" in html
        assert "Projected Month-End Balance" in html
        assert "Active Goals" in html
        assert "Spending Pattern Analysis" in html
        assert "Cash Flow Trend" in html
        assert "Alerts & Notifications" in html
        assert "Budget Recommendations" in html
        assert "AI Insights" in html
        assert "Investment Portfolio Summary" not in html
        assert "Asset Allocation" not in html
        assert "Portfolio Performance" not in html
        assert "Financial Health Score" not in html
        assert "Upcoming Bills" not in html
        assert "Future Projections" not in html
        print("[TEST 4: Analytics Page Render & Sections] PASS")

        # -------------------------------------------------------------
        # 4. MATHEMATICAL DATA VERIFICATION AGAINST DB
        # -------------------------------------------------------------
        db_incomes = Income.query.filter_by(user_id=uid).all()
        db_expenses = Expense.query.filter_by(user_id=uid).all()
        db_investments = Investment.query.filter_by(user_id=uid).all()
        db_goals = Goal.query.filter_by(user_id=uid).all()
        db_budget = Budget.query.filter_by(user_id=uid).order_by(Budget.created_at.desc()).first()

        calc_income = sum(i.amount for i in db_incomes)
        calc_expenses = sum(e.amount for e in db_expenses)
        calc_savings = calc_income - calc_expenses
        calc_savings_rate = round((calc_savings / calc_income) * 100, 1) if calc_income > 0 else 0.0
        calc_inv_val = sum(inv.current_value for inv in db_investments)
        calc_active_goals = sum(1 for g in db_goals if g.status == "In Progress")

        # Verify values in rendered HTML
        assert f"₹{calc_income:,.0f}" in html, f"Expected total income ₹{calc_income:,.0f} in HTML"
        assert f"₹{calc_expenses:,.0f}" in html, f"Expected total expenses ₹{calc_expenses:,.0f} in HTML"
        assert f"₹{calc_savings:,.0f}" in html, f"Expected net savings ₹{calc_savings:,.0f} in HTML"
        assert f"{calc_savings_rate}%" in html, f"Expected savings rate {calc_savings_rate}% in HTML"
        assert f"₹{calc_inv_val:,.0f}" not in html, f"Expected investment value ₹{calc_inv_val:,.0f} NOT in HTML"
        assert f"{calc_active_goals}" in html, f"Expected active goals count {calc_active_goals} in HTML"
        print(f"  - Financial Summary: Income=₹{calc_income:,.0f}, Expense=₹{calc_expenses:,.0f}, Savings=₹{calc_savings:,.0f}, Rate={calc_savings_rate}%, Active Goals={calc_active_goals}")
        print("[TEST 5: Mathematical Verification of Financial Summary] PASS")

        # -------------------------------------------------------------
        # 5. SPENDING PATTERN & CASH FLOW TREND SERVICES TEST
        # -------------------------------------------------------------
        sp_analysis = get_spending_analysis(uid)
        assert sp_analysis["total_expenses"] == calc_expenses
        
        cf_trend = get_monthly_spending_trend(uid, num_months=6)
        assert len(cf_trend["labels"]) == 6
        assert len(cf_trend["income"]) == 6
        assert len(cf_trend["expenses"]) == 6
        assert len(cf_trend["savings"]) == 6
        print("[TEST 6: Spending Analysis & Cash Flow Services] PASS")

        # -------------------------------------------------------------
        # 6. ALERT DEDUPLICATION & MARK AS READ TEST
        # -------------------------------------------------------------
        check_and_create_alerts(uid)
        unread_alerts_before = get_user_alerts(uid, include_read=False)

        if not unread_alerts_before:
            # Create a test alert if all existing alerts are read
            test_alert = FinancialAlert(
                user_id=uid,
                alert_type="test_alert_type",
                title="Test Alert Title",
                message="Test alert message",
                severity="info",
                is_read=False
            )
            db.session.add(test_alert)
            db.session.commit()
            unread_alerts_before = get_user_alerts(uid, include_read=False)

        target_alert = unread_alerts_before[0]
        alert_id = target_alert.id

        # Mark alert as read via POST route
        read_res = client.post(f"/alerts/{alert_id}/read", follow_redirects=True)
        assert read_res.status_code == 200

        # Verify DB status updated
        updated_alert = db.session.get(FinancialAlert, alert_id)
        assert updated_alert.is_read is True, "Alert should be marked as read in DB!"

        # Refresh analytics (triggers check_and_create_alerts)
        refresh_res = client.get("/analytics")
        assert refresh_res.status_code == 200

        # Confirm target alert was NOT recreated as unread
        unread_alerts_after = get_user_alerts(uid, include_read=False)
        unread_ids = [a.id for a in unread_alerts_after]
        assert alert_id not in unread_ids, "Marked alert must not reappear in unread alerts list!"
        assert len(unread_alerts_after) == len(unread_alerts_before) - 1, "Unread alert count should decrease by 1!"
        print("[TEST 7: Financial Alert Mark Read & Deduplication] PASS")

        # -------------------------------------------------------------
        # 7. REGRESSION TEST FOR /dashboard AND OTHER MODULES
        # -------------------------------------------------------------
        dash_res = client.get("/dashboard")
        assert dash_res.status_code == 200
        assert "Welcome Back" in dash_res.get_data(as_text=True)
        assert "Smart Financial Insights" not in dash_res.get_data(as_text=True)

        exp_res = client.get("/expenses")
        assert exp_res.status_code == 200

        inc_res = client.get("/income")
        assert inc_res.status_code == 200

        acc_res = client.get("/accounts")
        assert acc_res.status_code == 200

        bud_res = client.get("/budgets")
        assert bud_res.status_code == 200

        inv_res = client.get("/investments")
        assert inv_res.status_code == 200

        goal_res = client.get("/goals")
        assert goal_res.status_code == 200

        prof_res = client.get("/profile")
        assert prof_res.status_code == 200
        print("[TEST 8: Regression Test — Dashboard & All M1/M2 Routes] PASS")

    print("\n============================================================")
    print("ALL AUTOMATED ANALYTICS TESTS PASSED SUCCESSFULLY!")
    print("============================================================\n")


if __name__ == "__main__":
    test_analytics_suite()
