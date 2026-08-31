import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)

from app import app, init_db_schema
from extensions import db
from models import User, Expense, Income, Budget, Goal, Account, FinancialAlert
from services.spending_analysis import calculate_financial_health_score
from datetime import date

def run_verification():
    print("============================================================")
    print("RUNNING VERIFICATION: TASK 1 (HEALTH SCORE) & TASK 2 (BUDGET DELETE)")
    print("============================================================")

    client = app.test_client()

    with app.app_context():
        init_db_schema()

        # 1. User Auth & Session
        vicky_email = "vicky@gmail.com"
        user = User.query.filter_by(email=vicky_email).first()
        assert user is not None, "User vicky@gmail.com does not exist"

        login_res = client.post("/login", data={"email": vicky_email, "password": "Vicky@123"}, follow_redirects=True)
        assert login_res.status_code == 200, "Login failed"
        print("[AUTH] Logged in successfully as vicky@gmail.com")

        uid = user.id

        # -------------------------------------------------------------
        # TEST TASK 1: DYNAMIC FINANCIAL HEALTH SCORE
        # -------------------------------------------------------------
        print("\n--- TESTING TASK 1: FINANCIAL HEALTH SCORE ---")
        
        initial_health = calculate_financial_health_score(uid)
        print(f"  - Calculated Initial Health Score: {initial_health['score']}/100")
        print(f"  - Status Label: {initial_health['status_label']}")
        print(f"  - Explanation: {initial_health['summary_explanation']}")
        for p in initial_health['breakdown']:
            print(f"    * Pillar '{p['pillar']}': {p['score']}/{p['max_score']} ({p['note']})")

        assert 0 <= initial_health['score'] <= 100, "Health score out of bounds 0-100"
        assert initial_health['status_label'] in ["Excellent", "Stable", "Needs Attention", "At Risk"], "Invalid status label"

        # Verify Dashboard & Analytics UI rendering of Financial Health Score
        dash_res = client.get("/dashboard")
        assert dash_res.status_code == 200
        dash_html = dash_res.data.decode("utf-8")
        assert "Financial Health Score" in dash_html, "Health Score widget missing from Dashboard"
        assert f"{initial_health['score']}" in dash_html, "Score value missing from Dashboard"

        analytics_res = client.get("/analytics")
        assert analytics_res.status_code == 200
        analytics_html = analytics_res.data.decode("utf-8")
        assert "Dynamic Financial Health Score" in analytics_html, "Health Score card missing from Analytics"

        print("[TASK 1: FINANCIAL HEALTH SCORE] PASS")

        # -------------------------------------------------------------
        # TEST TASK 2: BUDGET DELETE FUNCTIONALITY
        # -------------------------------------------------------------
        print("\n--- TESTING TASK 2: BUDGET DELETE FUNCTIONALITY ---")

        # Ensure a test budget exists
        car_goal = Goal.query.filter_by(user_id=uid).first()
        budget_to_delete = Budget.query.filter_by(user_id=uid).first()
        
        if not budget_to_delete:
            new_b = Budget(monthly_budget=35000.0, month="August", year=2026, goal_id=car_goal.id if car_goal else None, user_id=uid)
            db.session.add(new_b)
            db.session.commit()
            budget_to_delete = new_b

        budget_id = budget_to_delete.id
        linked_goal_id = budget_to_delete.goal_id
        print(f"  - Target Budget ID to delete: {budget_id} (Linked Goal ID: {linked_goal_id})")

        # Perform POST request to delete route
        delete_res = client.post(f"/budgets/delete/{budget_id}", follow_redirects=True)
        assert delete_res.status_code == 200, f"Delete request failed with status {delete_res.status_code}"
        delete_html = delete_res.data.decode("utf-8")

        # 1. Confirm success message
        assert "Budget deleted successfully!" in delete_html, "Success flash message missing or incorrect!"
        print("  - Flash Message Check: PASS ('Budget deleted successfully!' displayed)")

        # 2. Confirm record is deleted from Database
        deleted_b_check = Budget.query.get(budget_id)
        assert deleted_b_check is None, f"Budget record {budget_id} still exists in Database after deletion!"
        print("  - Database Check: PASS (Budget record removed from database)")

        # 3. Confirm linked Goal remains completely intact
        if linked_goal_id:
            goal_check = Goal.query.get(linked_goal_id)
            assert goal_check is not None, f"Linked Goal {linked_goal_id} was accidentally deleted!"
            print(f"  - Linked Goal Integrity Check: PASS (Goal '{goal_check.goal_name}' remains intact)")

        # 4. Confirm Budget page no longer shows the deleted budget
        b_page_res = client.get("/budgets").data.decode("utf-8")
        assert "Update Budget" not in b_page_res, "Budget form still in 'Update' mode instead of reset"
        print("  - Budget Page Refresh Check: PASS")

        # 5. Confirm Health Score recalculated dynamically without errors
        post_delete_health = calculate_financial_health_score(uid)
        print(f"  - Health Score after budget deletion: {post_delete_health['score']}/100 ({post_delete_health['status_label']})")
        
        print("[TASK 3: BUDGET DELETE FUNCTIONALITY] PASS")

    print("\n============================================================")
    print("ALL VERIFICATION CHECKS FOR TASK 1 AND TASK 2 PASSED PERFECTLY!")
    print("============================================================")

if __name__ == "__main__":
    run_verification()
