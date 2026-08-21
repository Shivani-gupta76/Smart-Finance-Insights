from datetime import date, datetime
from extensions import db
from models.alert import FinancialAlert
from models.budget import Budget
from models.goal import Goal
from models.expense import Expense
from models.income import Income
from services.spending_analysis import get_spending_analysis


def check_and_create_alerts(user_id):
    """
    Evaluates real user financial events and creates user-specific alerts.
    Prevents duplicate unread alerts on dashboard refresh.
    """
    analysis = get_spending_analysis(user_id)
    goals = Goal.query.filter_by(user_id=user_id).all()
    today = date.today()

    new_alerts = []

    # Helper function to prevent duplicate alerts
    def add_alert_if_not_exists(alert_type, title, message, severity):
        existing = FinancialAlert.query.filter_by(
            user_id=user_id,
            alert_type=alert_type,
            title=title
        ).first()


        if not existing:
            alert = FinancialAlert(
                user_id=user_id,
                alert_type=alert_type,
                title=title,
                message=message,
                severity=severity,
                is_read=False
            )
            db.session.add(alert)
            new_alerts.append(alert)

    # 1. Budget Exceeded Alert
    if analysis["is_over_budget"]:
        over_amt = analysis["over_budget_amount"]
        add_alert_if_not_exists(
            alert_type="budget_exceeded",
            title="Monthly Budget Exceeded",
            message=f"Your monthly budget has been exceeded by ₹{over_amt:,.0f}.",
            severity="danger"
        )

    # 2. High Category Spending Alert (>40% of total expenses)
    if analysis["highest_spending_category"] and analysis["highest_spending_percentage"] >= 40.0:
        cat = analysis["highest_spending_category"]
        pct = analysis["highest_spending_percentage"]
        amt = analysis["highest_spending_amount"]
        add_alert_if_not_exists(
            alert_type="high_category_spending",
            title="High Category Spending",
            message=f"{cat} accounts for {pct}% of your total expenses (₹{amt:,.0f}).",
            severity="warning"
        )

    # 3. Significant Spending Increase (>15%)
    if analysis["spending_change_pct"] >= 15.0 and analysis["prev_month_expenses"] > 0:
        pct = analysis["spending_change_pct"]
        add_alert_if_not_exists(
            alert_type="spending_increase",
            title="Spending Increase Detected",
            message=f"Your monthly spending increased by {pct}% compared with last month.",
            severity="warning"
        )

    # 4. Low Savings / Negative Monthly Balance
    if analysis["total_income"] > 0 and analysis["total_savings"] < 0:
        add_alert_if_not_exists(
            alert_type="low_savings",
            title="Negative Net Balance",
            message=f"Your total expenses (₹{analysis['total_expenses']:,.0f}) exceed your total income (₹{analysis['total_income']:,.0f}).",
            severity="danger"
        )

    # 5. Goal Alerts
    for g in goals:
        if g.status == "In Progress" and g.target_date:
            days_left = (g.target_date - today).days

            # Goal deadline approaching (within 30 days)
            if 0 <= days_left <= 30:
                add_alert_if_not_exists(
                    alert_type=f"goal_deadline_{g.id}",
                    title="Goal Deadline Approaching",
                    message=f"Your '{g.goal_name}' goal deadline is in {days_left} days ({g.target_date.strftime('%d %b %Y')}).",
                    severity="warning"
                )
            elif days_left < 0:
                add_alert_if_not_exists(
                    alert_type=f"goal_past_due_{g.id}",
                    title="Goal Past Target Date",
                    message=f"Your '{g.goal_name}' goal target date was {abs(days_left)} days ago.",
                    severity="info"
                )

            # Low Goal Progress check
            if g.target_amount > 0:
                progress_pct = (g.current_amount / g.target_amount) * 100
                if days_left <= 60 and progress_pct < 40.0:
                    add_alert_if_not_exists(
                        alert_type=f"goal_low_progress_{g.id}",
                        title="Low Goal Progress",
                        message=f"Your savings (₹{g.current_amount:,.0f}) are below the expected target amount for '{g.goal_name}' ({progress_pct:.1f}% reached).",
                        severity="info"
                    )

    if new_alerts:
        db.session.commit()

    return new_alerts


def get_user_alerts(user_id, include_read=False):
    """
    Retrieves alerts for the logged-in user.
    """
    query = FinancialAlert.query.filter_by(user_id=user_id)
    if not include_read:
        query = query.filter_by(is_read=False)
    
    return query.order_by(FinancialAlert.created_at.desc()).all()


def mark_alert_as_read(alert_id, user_id):
    """
    Marks a specific alert as read for the user.
    """
    alert = FinancialAlert.query.filter_by(id=alert_id, user_id=user_id).first()
    if alert:
        alert.is_read = True
        db.session.commit()
        return True
    return False
