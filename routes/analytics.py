from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import date
from extensions import db
from models.budget import Budget
from models.goal import Goal
from models.expense import Expense

from services.spending_analysis import (
    get_spending_analysis,
    get_monthly_spending_trend,
    get_advanced_spending_patterns,
    get_rebuilt_analytics_data,
    get_goal_expense_analytics,
    calculate_financial_health_score
)
from services.alert_service import check_and_create_alerts, get_user_alerts

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
@login_required
def analytics():
    user_id = current_user.id

    # 1. Trigger Alert Check
    check_and_create_alerts(user_id)
    alerts = get_user_alerts(user_id, include_read=False)

    # 2. Financial Metrics & KPI Data
    rebuilt_data = get_rebuilt_analytics_data(user_id)
    spending_analysis = get_spending_analysis(user_id)
    cash_flow_trend = get_monthly_spending_trend(user_id, num_months=6)
    advanced_patterns = get_advanced_spending_patterns(user_id)
    goal_expense_analytics = get_goal_expense_analytics(user_id)
    health_score = calculate_financial_health_score(user_id)

    # 3. Budget Analytics & Linked Goal Relationships
    budgets = Budget.query.filter_by(user_id=user_id).all()
    user_expenses = Expense.query.filter_by(user_id=user_id).all()

    budget_analytics_list = []
    highest_usage_budget = None
    most_exceeded_budget = None
    max_usage_pct = -1.0
    max_exceeded_amt = -1.0

    for b in budgets:
        b_month_num = date.today().month
        actual_spent = sum(
            e.amount for e in user_expenses
            if e.expense_date and e.expense_date.month == b_month_num
        )
        # Category specific spending if linked to goal category
        if b.goal and b.goal.category:
            cat_spent = sum(e.amount for e in user_expenses if e.category.lower() == b.goal.category.lower())
            if cat_spent > 0:
                actual_spent = cat_spent

        usage_pct = round((actual_spent / b.monthly_budget) * 100, 1) if b.monthly_budget > 0 else 0.0
        rem_amount = b.monthly_budget - actual_spent

        if usage_pct < 50.0:
            status = "Healthy"
            status_class = "healthy"
        elif usage_pct < 80.0:
            status = "Normal"
            status_class = "normal"
        elif usage_pct < 100.0:
            status = "Warning"
            status_class = "warning"
        else:
            status = "Exceeded"
            status_class = "exceeded"

        if usage_pct > max_usage_pct:
            max_usage_pct = usage_pct
            highest_usage_budget = b.month

        if actual_spent > b.monthly_budget:
            exceeded_diff = actual_spent - b.monthly_budget
            if exceeded_diff > max_exceeded_amt:
                max_exceeded_amt = exceeded_diff
                most_exceeded_budget = b.month

        # Related expenses for linked budget/goal
        related_expenses = []
        if b.goal and b.goal.category:
            related_expenses = [e for e in user_expenses if e.category.lower() == b.goal.category.lower()][:5]

        budget_analytics_list.append({
            "budget": b,
            "actual_spent": actual_spent,
            "rem_amount": rem_amount,
            "usage_pct": usage_pct,
            "status": status,
            "status_class": status_class,
            "linked_goal": b.goal,
            "related_expenses": related_expenses
        })

    # 4. Goal Analytics
    goals = Goal.query.filter_by(user_id=user_id).all()
    goal_analytics_list = []
    completed_count = 0
    active_count = 0
    near_completion_count = 0

    for g in goals:
        prog_pct = round((g.current_amount / g.target_amount) * 100, 1) if g.target_amount > 0 else 0.0
        rem_amt = max(0.0, g.target_amount - g.current_amount)

        if g.status == "Completed" or prog_pct >= 100.0:
            completed_count += 1
        else:
            active_count += 1
            if prog_pct >= 75.0:
                near_completion_count += 1

        goal_analytics_list.append({
            "goal": g,
            "prog_pct": prog_pct,
            "rem_amt": rem_amt
        })

    return render_template(
        "analytics.html",
        rebuilt_data=rebuilt_data,
        spending_analysis=spending_analysis,
        cash_flow_trend=cash_flow_trend,
        advanced_patterns=advanced_patterns,
        goal_expense_analytics=goal_expense_analytics,
        alerts=alerts,
        budget_analytics_list=budget_analytics_list,
        highest_usage_budget=highest_usage_budget,
        most_exceeded_budget=most_exceeded_budget,
        goal_analytics_list=goal_analytics_list,
        completed_count=completed_count,
        active_count=active_count,
        near_completion_count=near_completion_count,
        health_score=health_score
    )
