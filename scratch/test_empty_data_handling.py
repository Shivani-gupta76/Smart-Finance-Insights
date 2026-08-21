import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)

from app import app
from services.spending_analysis import get_advanced_spending_patterns

def test_empty_user():
    with app.app_context():
        # User ID 999999 (non-existent user with 0 expenses)
        result = get_advanced_spending_patterns(999999)
        print("Empty User Result:")
        print("  - 6M Trend has_data:", result["monthly_trend_6m"]["has_data"])
        print("  - 3M Cat Analysis has_data:", result["category_analysis_3m"]["has_data"])
        print("  - Weekly Pattern has_data:", result["weekly_pattern"]["has_data"])
        print("  - Month vs Prev has_prev_data:", result["month_vs_prev"]["has_prev_data"])
        print("  - Anomalies:", result["anomalies"])
        assert result["monthly_trend_6m"]["has_data"] is False
        assert result["category_analysis_3m"]["has_data"] is False
        assert result["weekly_pattern"]["has_data"] is False
        assert result["month_vs_prev"]["has_prev_data"] is False
        assert len(result["anomalies"]) == 0
        print("EMPTY DATA HANDLING TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_empty_user()
