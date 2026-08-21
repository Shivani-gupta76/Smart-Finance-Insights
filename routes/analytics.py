from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db

from services.spending_analysis import (
    get_spending_analysis,
    get_monthly_spending_trend,
    get_rebuilt_analytics_data
)
from services.alert_service import check_and_create_alerts, get_user_alerts

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
@login_required
def analytics():
    user_id = current_user.id

    # 1. Calculate Rebuilt Analytics KPI & Section Data
    rebuilt_data = get_rebuilt_analytics_data(user_id)

    # 2. Spending Pattern Analysis & Category Breakdown
    spending_analysis = get_spending_analysis(user_id)

    # 3. 6-Month Cash Flow Trend
    cash_flow_trend = get_monthly_spending_trend(user_id, num_months=6)

    # 4. Financial Alerts & Notifications
    check_and_create_alerts(user_id)
    alerts = get_user_alerts(user_id, include_read=False)

    return render_template(
        "analytics.html",
        rebuilt_data=rebuilt_data,
        spending_analysis=spending_analysis,
        cash_flow_trend=cash_flow_trend,
        alerts=alerts
    )
