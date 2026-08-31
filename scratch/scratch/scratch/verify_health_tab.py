import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)

from app import app, init_db_schema
from models import User

def verify_health_tab():
    print("============================================================")
    print("VERIFYING FINANCIAL HEALTH SCORE TAB ON ANALYTICS PAGE")
    print("============================================================")

    client = app.test_client()

    with app.app_context():
        init_db_schema()

        # Login
        user = User.query.filter_by(email="vicky@gmail.com").first()
        assert user is not None, "User vicky@gmail.com does not exist"

        login_res = client.post("/login", data={"email": "vicky@gmail.com", "password": "Vicky@123"}, follow_redirects=True)
        assert login_res.status_code == 200

        # Request Analytics page
        analytics_res = client.get("/analytics")
        assert analytics_res.status_code == 200, f"Analytics page failed with status {analytics_res.status_code}"

        html = analytics_res.data.decode("utf-8")

        # 1. Check Tab Navigation Order
        assert "switchTab('health')" in html, "Financial Health Score tab button missing"
        assert "Financial Health Score" in html, "Financial Health Score tab title missing"
        print("[CHECK 1: TAB BUTTON] PASS (Tab button switchTab('health') present)")

        # 2. Check Tab Container
        assert 'id="tab-health"' in html, "tab-health div container missing"
        print("[CHECK 2: TAB CONTAINER] PASS (id='tab-health' container present)")

        # 3. Check Overall Financial Health Score & Status
        assert "Overall Financial Health Score" in html, "Overall score header missing"
        assert "Status: Excellent" in html or "Status:" in html, "Health status missing"
        assert "out of 100" in html, "Score out of 100 indicator missing"
        print("[CHECK 3: OVERALL SCORE & STATUS] PASS")

        # 4. Check Visual Gauge
        assert "Visual Score Index Gauge" in html, "Visual gauge label missing"
        print("[CHECK 4: VISUAL GAUGE] PASS")

        # 5. Check 5 Component Scores
        assert "Savings Health" in html, "Savings Health component score missing"
        assert "Budget Health" in html, "Budget Health component score missing"
        assert "Goal Progress" in html, "Goal Progress component score missing"
        assert "Spending Health" in html, "Spending Health component score missing"
        assert "Risk & Alerts" in html, "Risk & Alerts component score missing"
        print("[CHECK 5: 5 COMPONENT SCORES] PASS")

        # 6. Check Positive Factors & Areas Needing Improvement
        assert "Positive Financial Factors" in html, "Positive Financial Factors section missing"
        assert "Areas Needing Improvement" in html, "Areas Needing Improvement section missing"
        print("[CHECK 6: POSITIVE FACTORS & IMPROVEMENT AREAS] PASS")

        # 7. Check Dynamic Recommendations
        assert "Dynamic Recommendations to Improve Score" in html, "Dynamic Recommendations section missing"
        print("[CHECK 7: DYNAMIC RECOMMENDATIONS] PASS")

    print("\n============================================================")
    print("ALL FINANCIAL HEALTH SCORE TAB VERIFICATION CHECKS PASSED!")
    print("============================================================")

if __name__ == "__main__":
    verify_health_tab()
