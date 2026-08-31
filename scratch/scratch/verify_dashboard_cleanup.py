import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)

from app import app, init_db_schema
from models import User

def verify_dashboard_cleanup():
    print("============================================================")
    print("RUNNING COMPLETE VERIFICATION FOR DASHBOARD CLEANUP")
    print("============================================================")

    client = app.test_client()

    with app.app_context():
        init_db_schema()

        # Login
        user = User.query.filter_by(email="vicky@gmail.com").first()
        assert user is not None, "User vicky@gmail.com does not exist"

        login_res = client.post("/login", data={"email": "vicky@gmail.com", "password": "Vicky@123"}, follow_redirects=True)
        assert login_res.status_code == 200, "Login failed"

        # -------------------------------------------------------------
        # 1. VERIFY DASHBOARD CLEANUP
        # -------------------------------------------------------------
        dash_res = client.get("/dashboard")
        assert dash_res.status_code == 200, f"Dashboard failed with status {dash_res.status_code}"

        dash_html = dash_res.data.decode("utf-8")

        # Confirm Alerts section removed from Dashboard UI
        assert "smart-alerts-container" not in dash_html, "Alerts container still present on Dashboard UI!"
        assert "btn-dismiss-alert" not in dash_html, "Dismiss alert buttons still present on Dashboard UI!"
        print("[CHECK 1: ALERTS REMOVED FROM DASHBOARD] PASS")

        # Confirm Financial Health Score widget removed from Dashboard UI
        assert "Financial Health Score:" not in dash_html, "Financial Health Score header still present on Dashboard UI!"
        assert "Health Index Gauge" not in dash_html, "Health Index Gauge still present on Dashboard UI!"
        print("[CHECK 2: FINANCIAL HEALTH SCORE REMOVED FROM DASHBOARD] PASS")

        # Confirm core Dashboard components remain intact
        assert "Welcome Back, Vicky" in dash_html, "Welcome banner missing"
        assert "Total Income" in dash_html, "Total Income card missing"
        assert "Total Expenses" in dash_html, "Total Expenses card missing"
        assert "Total Savings" in dash_html, "Total Savings card missing"
        assert "Monthly Budget" in dash_html, "Monthly Budget card missing"
        print("[CHECK 3: CORE DASHBOARD UI INTACT] PASS")

        # -------------------------------------------------------------
        # 2. VERIFY ALERTS SIDEBAR PAGE REMAINS FUNCTIONAL
        # -------------------------------------------------------------
        alerts_res = client.get("/alerts")
        assert alerts_res.status_code == 200, f"Alerts page failed with status {alerts_res.status_code}"
        alerts_html = alerts_res.data.decode("utf-8")
        assert "Financial Alerts" in alerts_html, "Alerts page title missing"
        print("[CHECK 4: ALERTS PAGE FULLY FUNCTIONAL] PASS")

        # -------------------------------------------------------------
        # 3. VERIFY FINANCIAL HEALTH SCORE IN ANALYTICS REMAINS FUNCTIONAL
        # -------------------------------------------------------------
        analytics_res = client.get("/analytics")
        assert analytics_res.status_code == 200, f"Analytics page failed with status {analytics_res.status_code}"
        analytics_html = analytics_res.data.decode("utf-8")

        assert "switchTab('health')" in analytics_html, "Financial Health Score tab button missing from Analytics"
        assert 'id="tab-health"' in analytics_html, "Financial Health Score tab container missing from Analytics"
        assert "Overall Financial Health Score" in analytics_html, "Overall Financial Health Score header missing from Analytics"
        assert "Component Score Breakdown" in analytics_html, "Component Score Breakdown missing from Analytics"
        print("[CHECK 5: FINANCIAL HEALTH SCORE TAB IN ANALYTICS FULLY FUNCTIONAL] PASS")

    print("\n============================================================")
    print("ALL VERIFICATION CHECKS PASSED PERFECTLY!")
    print("============================================================")

if __name__ == "__main__":
    verify_dashboard_cleanup()
