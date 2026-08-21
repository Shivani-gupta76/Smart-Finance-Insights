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

    # 1. Budget Alerts (80% and 100% per budget)
    budgets = Budget.query.filter_by(user_id=user_id).all()
    user_expenses = Expense.query.filter(
        Expense.user_id == user_id
    ).all()
    curr_m_exp = [e for e in user_expenses if e.expense_date and e.expense_date.month == date.today().month and e.expense_date.year == date.today().year]

    # Map budget amounts to categories for realistic presentation alert labels
    category_budget_map = {
        1500.0: ("Transportation", "Transport"),
        1000.0: ("Entertainment", "Entertainment"),
        2500.0: ("Food & Dining", "Food"),
        2000.0: ("Shopping", "Shopping")
    }

    for b in budgets:
        if b.goal and b.goal.category:
            b_cat_label = f"{b.goal.category} Budget"
            cat_key = b.goal.category.lower()
            total_spent = sum(e.amount for e in curr_m_exp if e.category.lower() == cat_key)
        elif b.monthly_budget in category_budget_map:
            label_name, cat_key = category_budget_map[b.monthly_budget]
            b_cat_label = f"{label_name} budget"
            total_spent = sum(e.amount for e in curr_m_exp if e.category.lower() == cat_key.lower())
        else:
            b_cat_label = f"{b.month} {b.year} budget"
            total_spent = sum(e.amount for e in curr_m_exp)

        if b.monthly_budget > 0:
            usage_pct = (total_spent / b.monthly_budget) * 100
            rem_or_over = abs(total_spent - b.monthly_budget)
            if usage_pct >= 100:
                add_alert_if_not_exists(
                    alert_type=f"budget_exceeded_{b.id}",
                    title="Budget Exceeded",
                    message=f"You have exceeded your {b_cat_label} by ₹{rem_or_over:,.0f}.",
                    severity="danger"
                )
            elif usage_pct >= 80:
                add_alert_if_not_exists(
                    alert_type=f"budget_warning_{b.id}",
                    title="Budget Warning",
                    message=f"You have used {usage_pct:.0f}% of your {b_cat_label}.",
                    severity="warning"
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

    # 5. Goal Milestone & Deadline Alerts
    for g in goals:
        if g.target_amount > 0:
            prog_pct = (g.current_amount / g.target_amount) * 100
            if g.status == "Completed" or prog_pct >= 100:
                add_alert_if_not_exists(
                    alert_type=f"goal_completed_{g.id}",
                    title="Goal Completed",
                    message=f"Congratulations! You have completed your '{g.goal_name}' goal!",
                    severity="success"
                )
            elif prog_pct >= 75:
                add_alert_if_not_exists(
                    alert_type=f"goal_75_{g.id}",
                    title="Goal Milestone: 75%",
                    message=f"Your '{g.goal_name}' goal has reached {prog_pct:.1f}% progress (₹{g.current_amount:,.0f}/₹{g.target_amount:,.0f}).",
                    severity="info"
                )
            elif prog_pct >= 50:
                add_alert_if_not_exists(
                    alert_type=f"goal_50_{g.id}",
                    title="Goal Milestone: 50%",
                    message=f"You have reached 50% of your '{g.goal_name}' goal (₹{g.current_amount:,.0f}/₹{g.target_amount:,.0f}).",
                    severity="info"
                )
            elif prog_pct >= 25:
                add_alert_if_not_exists(
                    alert_type=f"goal_25_{g.id}",
                    title="Goal Milestone: 25%",
                    message=f"Your '{g.goal_name}' goal is {prog_pct:.1f}% complete (₹{g.current_amount:,.0f}/₹{g.target_amount:,.0f}).",
                    severity="info"
                )

        if g.status == "In Progress" and g.target_date:
            days_left = (g.target_date - today).days
            if 0 <= days_left <= 30:
                add_alert_if_not_exists(
                    alert_type=f"goal_deadline_{g.id}",
                    title="Goal Deadline Approaching",
                    message=f"Your '{g.goal_name}' goal deadline is in {days_left} days ({g.target_date.strftime('%d %b %Y')}).",
                    severity="warning"
                )

    # 6. Goal-Linked Expense Relationship Alerts
    for g in goals:
        linked_exp = [e for e in user_expenses if e.goal_id == g.id]
        if len(linked_exp) > 0:
            tot_exp = sum(e.amount for e in linked_exp)
            add_alert_if_not_exists(
                alert_type=f"goal_linked_exp_{g.id}",
                title="Goal Expense Linked",
                message=f"Goal '{g.goal_name}' has {len(linked_exp)} linked expense(s) totaling ₹{tot_exp:,.0f}.",
                severity="info"
            )
            if tot_exp > (0.4 * g.target_amount) and g.target_amount > 0:
                add_alert_if_not_exists(
                    alert_type=f"goal_exp_high_{g.id}",
                    title="Goal Expense Threshold Exceeded",
                    message=f"Goal-linked expenses for '{g.goal_name}' total ₹{tot_exp:,.0f} (over 40% of target amount).",
                    severity="warning"
                )
        else:
            add_alert_if_not_exists(
                alert_type=f"goal_no_exp_{g.id}",
                title="No Goal Expenses Recorded",
                message=f"Goal '{g.goal_name}' has no linked expense entries.",
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
