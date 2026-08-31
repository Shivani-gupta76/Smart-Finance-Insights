from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from datetime import datetime


from extensions import db
from models.alert import FinancialAlert
from services.alert_service import check_and_create_alerts, mark_alert_as_read

alert_bp = Blueprint("alert", __name__)


@alert_bp.route("/alerts")
@login_required
def alerts():
    user_id = current_user.id

    # 1. Trigger Alert Check
    check_and_create_alerts(user_id)


    # 2. Date & Type Filter Handling
    from_date_str = request.args.get("from_date", "").strip()
    to_date_str = request.args.get("to_date", "").strip()

    query = FinancialAlert.query.filter_by(user_id=user_id)

    if from_date_str:
        try:
            f_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
            query = query.filter(FinancialAlert.created_at >= f_date)
        except ValueError:
            pass

    if to_date_str:
        try:
            t_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()
            t_datetime = datetime.combine(t_date, datetime.max.time())
            query = query.filter(FinancialAlert.created_at <= t_datetime)
        except ValueError:
            pass

    all_user_alerts = query.order_by(FinancialAlert.created_at.desc()).all()



    # 3. Calculate Summary Statistics
    total_alerts = len(all_user_alerts)
    unread_alerts = sum(1 for a in all_user_alerts if not a.is_read)
    critical_alerts = sum(1 for a in all_user_alerts if a.severity in ["danger", "critical"])
    resolved_alerts = sum(1 for a in all_user_alerts if a.is_read)

    # 4. Filter Handling
    active_filter = request.args.get("filter", "all").lower()

    if active_filter == "unread":
        filtered_alerts = [a for a in all_user_alerts if not a.is_read]
    elif active_filter == "budget":
        filtered_alerts = [a for a in all_user_alerts if "budget" in a.alert_type.lower() or "budget" in a.title.lower()]
    elif active_filter == "goal":
        filtered_alerts = [a for a in all_user_alerts if "goal" in a.alert_type.lower() or "goal" in a.title.lower()]
    elif active_filter == "spending":

        filtered_alerts = [
            a for a in all_user_alerts
            if "spending" in a.alert_type.lower()
            or "spending" in a.title.lower()
            or "low_savings" in a.alert_type.lower()
            or "savings" in a.title.lower()
            or "balance" in a.title.lower()
        ]

        

    elif active_filter == "critical":
        filtered_alerts = [a for a in all_user_alerts if a.severity in ["danger", "critical"]]
    else:
        filtered_alerts = all_user_alerts

    return render_template(
        "alerts.html",
        alerts=filtered_alerts,
        active_filter=active_filter,

        from_date=from_date_str,
        to_date=to_date_str,


        total_alerts=total_alerts,
        unread_alerts=unread_alerts,
        critical_alerts=critical_alerts,
        resolved_alerts=resolved_alerts
    )


@alert_bp.route("/alerts/<int:alert_id>/toggle-read", methods=["POST"])
@login_required
def toggle_alert_read(alert_id):
    alert_obj = FinancialAlert.query.filter_by(id=alert_id, user_id=current_user.id).first_or_404()
    alert_obj.is_read = not alert_obj.is_read
    db.session.commit()
    status_label = "read" if alert_obj.is_read else "unread"
    flash(f"Alert marked as {status_label}.", "success")
    return redirect(request.referrer or url_for("alert.alerts"))
