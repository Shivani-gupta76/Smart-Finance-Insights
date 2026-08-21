import os
import sys

# Force UTF-8 stdout encoding for Windows console test run
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)

from app import app, init_db_schema
from extensions import db, bcrypt
from models import User, Expense, Income, Budget, Goal, GoalPart, Investment, Account, FinancialAlert
from services.spending_analysis import get_spending_analysis, get_monthly_spending_trend
from services.alert_service import check_and_create_alerts, get_user_alerts, mark_alert_as_read
from datetime import date, timedelta

def run_tests():
    print("=" * 60)
    print("STARTING MILESTONE 3 PART 1 REGRESSION & FUNCTIONAL TESTS")
    print("=" * 60)

    with app.app_context():
        # 1. Initialize schema (Runs safe ALTER TABLE if needed)
        init_db_schema()
        print("[OK] Database schema verified successfully.")

        # 2. Setup Test User
        test_email = "m3_test_user@finsight.com"
        user = User.query.filter_by(email=test_email).first()
        if not user:
            pw_hash = bcrypt.generate_password_hash("testpass123").decode("utf-8")
            user = User(full_name="Milestone3 Test User", email=test_email, password=pw_hash)
            db.session.add(user)
            db.session.commit()
            print(f"[OK] Created test user (ID: {user.id})")
        else:
            print(f"[OK] Found existing test user (ID: {user.id})")

        uid = user.id

        # Clean old test data for this test user
        Expense.query.filter_by(user_id=uid).delete()
        Income.query.filter_by(user_id=uid).delete()
        Budget.query.filter_by(user_id=uid).delete()
        Goal.query.filter_by(user_id=uid).delete()
        Account.query.filter_by(user_id=uid).delete()
        FinancialAlert.query.filter_by(user_id=uid).delete()
        db.session.commit()

        # 3. Create Account
        account = Account(account_name="Primary Savings", account_type="Bank", balance=50000.0, user_id=uid)
        db.session.add(account)
        db.session.commit()
        print("[OK] Created primary bank account.")

        # 4. Test Goal Creation & Budget Linking
        car_goal = Goal(
            goal_name="Buy a Car",
            goal_type="Savings",
            target_amount=500000.0,
            current_amount=50000.0,
            target_date=date.today() + timedelta(days=20),
            category="Vehicle",
            priority="High",
            status="In Progress",
            user_id=uid
        )
        db.session.add(car_goal)
        db.session.commit()
        print(f"[OK] Created Goal: '{car_goal.goal_name}' (ID: {car_goal.id})")

        # Create Budget linked to Goal
        car_budget = Budget(
            monthly_budget=30000.0,
            month="August",
            year=2026,
            goal_id=car_goal.id,
            user_id=uid
        )
        db.session.add(car_budget)
        db.session.commit()
        print(f"[OK] Created Budget of ₹{car_budget.monthly_budget} linked to Goal '{car_goal.goal_name}'")

        # Verify Goal-Budget relationship
        fetched_budget = Budget.query.filter_by(user_id=uid).first()
        assert fetched_budget.goal_id == car_goal.id, "Budget.goal_id should match car_goal.id"
        assert fetched_budget.goal.goal_name == "Buy a Car", "Budget.goal relationship should resolve Goal object"
        print("[OK] Verified Budget -> Goal relationship!")

        # 5. Add Income & Expenses
        inc1 = Income(title="Salary", source="Job", amount=60000.0, income_date=date.today(), user_id=uid)
        db.session.add(inc1)

        exp1 = Expense(
            title="Grocery Shopping",
            category="Food",
            amount=20000.0,
            payment_method="UPI",
            account_id=account.id,
            expense_date=date.today(),
            user_id=uid
        )
        exp2 = Expense(
            title="Fuel",
            category="Transport",
            amount=12000.0,
            payment_method="Card",
            account_id=account.id,
            expense_date=date.today(),
            user_id=uid
        )
        db.session.add_all([exp1, exp2])
        db.session.commit()
        print("[OK] Created Income (₹60,000) and Expenses (Food: ₹20,000, Transport: ₹12,000, Total Expenses: ₹32,000).")

        # 6. Verify Spending Pattern Analysis
        analysis = get_spending_analysis(uid)
        print("\n--- SPENDING ANALYSIS RESULTS ---")
        print(f"Total Income: ₹{analysis['total_income']:,.2f}")
        print(f"Total Expenses: ₹{analysis['total_expenses']:,.2f}")
        print(f"Total Savings: ₹{analysis['total_savings']:,.2f}")
        print(f"Highest Category: {analysis['highest_spending_category']} (₹{analysis['highest_spending_amount']:,.2f}, {analysis['highest_spending_percentage']}%)")
        print(f"Is Over Budget: {analysis['is_over_budget']} (Budget: ₹{analysis['monthly_budget_amount']}, Over by: ₹{analysis['over_budget_amount']})")
        print("Explainable Insights:")
        for ins in analysis["insights"]:
            print(f"  - {ins}")

        assert analysis["total_income"] == 60000.0
        assert analysis["total_expenses"] == 32000.0
        assert analysis["total_savings"] == 28000.0
        assert analysis["highest_spending_category"] == "Food"
        assert analysis["is_over_budget"] == True
        assert analysis["over_budget_amount"] == 2000.0
        print("[OK] Spending Pattern Analysis assertions PASSED!")

        # 7. Verify 6-Month Trend Data
        trend = get_monthly_spending_trend(uid, num_months=6)
        print("\n--- 6-MONTH TREND DATA ---")
        print(f"Labels: {trend['labels']}")
        print(f"Income: {trend['income']}")
        print(f"Expenses: {trend['expenses']}")
        print(f"Savings: {trend['savings']}")
        assert len(trend["labels"]) == 6
        print("[OK] 6-Month Trend Service PASSED!")

        # 8. Verify Alert System & Deduplication
        new_alerts = check_and_create_alerts(uid)
        print(f"\n[OK] Generated {len(new_alerts)} alerts:")
        alerts = get_user_alerts(uid)
        for a in alerts:
            print(f"  [{a.severity.upper()}] {a.title}: {a.message}")

        assert len(alerts) > 0, "Alerts should be created for budget overrun and approaching goal deadline"

        # Check deduplication: run alert check again immediately
        second_run_alerts = check_and_create_alerts(uid)
        assert len(second_run_alerts) == 0, "Deduplication failed: Duplicate unread alerts were created!"
        print("[OK] Alert deduplication test PASSED! No duplicate alerts created on refresh.")

        # Test marking alert as read
        alert_to_read = alerts[0]
        read_success = mark_alert_as_read(alert_to_read.id, uid)
        assert read_success == True
        remaining_unread = get_user_alerts(uid, include_read=False)
        assert len(remaining_unread) == len(alerts) - 1
        print(f"[OK] Marked alert '{alert_to_read.title}' as read successfully!")

        # 9. ADJUSTMENT #1 TEST: Delete Goal, Verify Budget is NOT deleted
        print("\n--- TESTING ADJUSTMENT #1: GOAL DELETION DOES NOT DELETE BUDGET ---")
        goal_id_to_del = car_goal.id
        db.session.delete(car_goal)
        db.session.commit()

        # Check if Budget still exists!
        budget_after_goal_del = Budget.query.filter_by(user_id=uid).first()
        assert budget_after_goal_del is not None, "Budget MUST NOT be deleted when Goal is deleted!"
        print(f"[OK] Goal deleted successfully. Linked budget (ID: {budget_after_goal_del.id}) still exists with goal_id={budget_after_goal_del.goal_id}.")

        # Clean up test user data
        Expense.query.filter_by(user_id=uid).delete()
        Income.query.filter_by(user_id=uid).delete()
        Budget.query.filter_by(user_id=uid).delete()
        Account.query.filter_by(user_id=uid).delete()
        FinancialAlert.query.filter_by(user_id=uid).delete()
        User.query.filter_by(id=uid).delete()
        db.session.commit()
        print("[OK] Test user and data cleaned up.")

    print("\n" + "=" * 60)
    print("ALL MILESTONE 3 TESTS PASSED SUCCESSFULLY! REGRESSION CHECKS CLEAN.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
