from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import date
from extensions import db
from models.budget import Budget
from models.goal import Goal
from models.expense import Expense
from models.income import Income

from services.spending_analysis import (
    get_spending_analysis,
    get_monthly_spending_trend,
    get_advanced_spending_patterns,
    get_rebuilt_analytics_data,
    get_goal_expense_analytics,
    calculate_financial_health_score,
    get_spending_analysis_periods,
    get_last_day_of_month
)
from services.alert_service import check_and_create_alerts, get_user_alerts

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
@login_required
def analytics():
    user_id = current_user.id
    today = date.today()
    current_month_name = today.strftime("%B")
    current_year = today.year

    # Extract month and year parameters (support both 'month'/'year' and 'rec_month'/'rec_year')
    sel_month = request.args.get("month", "").strip() or request.args.get("rec_month", "").strip() or current_month_name
    try:
        sel_year = int(request.args.get("year") or request.args.get("rec_year") or current_year)
    except (ValueError, TypeError):
        sel_year = current_year

    # 1. Trigger Alert Check
    check_and_create_alerts(user_id)
    alerts = get_user_alerts(user_id, include_read=False)

    # 2. Financial Metrics & KPI Data for Selected Month/Year
    rebuilt_data = get_rebuilt_analytics_data(user_id, sel_month, sel_year)
    spending_analysis = get_spending_analysis(user_id, sel_month, sel_year)
    spending_periods_data = get_spending_analysis_periods(user_id, sel_month, sel_year)
    cash_flow_trend = get_monthly_spending_trend(user_id, num_months=6)
    advanced_patterns = get_advanced_spending_patterns(user_id)
    goal_expense_analytics = get_goal_expense_analytics(user_id, sel_month, sel_year)
    health_score = calculate_financial_health_score(user_id, sel_month, sel_year)

    # 3. Budget Analytics & Month Selection for Budget Recommendations
    rec_month = sel_month
    rec_year = sel_year

    month_name_to_num = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
    }
    rec_month_num = month_name_to_num.get(rec_month.lower(), today.month)

    # Fetch budget specifically for rec_month + rec_year
    rec_budget = Budget.query.filter(
        Budget.user_id == user_id,
        db.func.lower(Budget.month) == rec_month.lower(),
        Budget.year == rec_year
    ).first()

    user_expenses = Expense.query.filter_by(user_id=user_id).all()
    start_date_rec = date(rec_year, rec_month_num, 1)
    last_day_rec = get_last_day_of_month(start_date_rec)

    if rec_year == current_year and rec_month_num == today.month:
        end_date_rec = min(today, last_day_rec)
    else:
        end_date_rec = last_day_rec

    rec_month_expenses = sum(
        e.amount for e in user_expenses
        if e.expense_date and start_date_rec <= e.expense_date <= end_date_rec
    )

    rec_budget_info = None
    rec_rule_recommendations = []

    if rec_budget and rec_budget.monthly_budget > 0:
        b_limit = rec_budget.monthly_budget
        usage_pct = round((rec_month_expenses / b_limit) * 100, 1)
        rem_amount = b_limit - rec_month_expenses
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

        rec_budget_info = {
            "has_budget": True,
            "budget": rec_budget,
            "actual_spent": rec_month_expenses,
            "rem_amount": rem_amount,
            "usage_pct": usage_pct,
            "status": status,
            "status_class": status_class,
            "linked_goal": rec_budget.goal
        }

        if usage_pct > 100:
            rec_rule_recommendations.append(
                f"High Budget Utilization: You have exceeded your {rec_month} {rec_year} budget (₹{rec_month_expenses:,.0f} spent out of ₹{b_limit:,.0f}). Consider pausing non-essential expenses."
            )
        elif usage_pct >= 75:
            rec_rule_recommendations.append(
                f"Budget Caution: You have utilized {usage_pct}% of your {rec_month} {rec_year} budget. Keep an eye on remaining funds (₹{rem_amount:,.0f} left)."
            )
        else:
            rec_rule_recommendations.append(
                f"Budget Discipline: Good progress! You have used {usage_pct}% of your ₹{b_limit:,.0f} budget for {rec_month} {rec_year}."
            )
    else:
        rec_budget_info = {
            "has_budget": False,
            "budget": None,
            "actual_spent": rec_month_expenses,
            "rem_amount": 0.0,
            "usage_pct": 0.0,
            "status": "No Budget Set",
            "status_class": "normal",
            "linked_goal": None
        }
        rec_rule_recommendations.append(
            f"No Monthly Budget Set: No active budget is recorded for {rec_month} {rec_year}. Set a budget on the Budget page to monitor spending."
        )

    # Category recommendations for rec_month
    rec_cat_totals = {}
    for e in user_expenses:
        if e.expense_date and start_date_rec <= e.expense_date <= end_date_rec:
            rec_cat_totals[e.category] = rec_cat_totals.get(e.category, 0.0) + e.amount

    sorted_rec_cats = sorted(rec_cat_totals.items(), key=lambda x: x[1], reverse=True)
    if sorted_rec_cats and rec_month_expenses > 0:
        top_c, top_a = sorted_rec_cats[0]
        top_p = round((top_a / rec_month_expenses) * 100, 1)
        if top_p >= 30.0:
            rec_rule_recommendations.append(
                f"Category Recommendation for {rec_month}: {top_c} accounts for {top_p}% of your expenses this month (₹{top_a:,.0f}). Capping {top_c} orders could increase savings."
            )

    # All budgets list for general overview
    budgets = Budget.query.filter_by(user_id=user_id).all()
    budget_analytics_list = []
    for b in budgets:
        b_m_num = month_name_to_num.get(b.month.lower(), today.month)
        b_start = date(b.year, b_m_num, 1)
        b_last = get_last_day_of_month(b_start)
        if b.year == current_year and b_m_num == today.month:
            b_end = min(today, b_last)
        else:
            b_end = b_last

        actual_spent = sum(
            e.amount for e in user_expenses
            if e.expense_date and b_start <= e.expense_date <= b_end
        )
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

        budget_analytics_list.append({
            "budget": b,
            "actual_spent": actual_spent,
            "rem_amount": rem_amount,
            "usage_pct": usage_pct,
            "status": status,
            "status_class": status_class,
            "linked_goal": b.goal
        })

    # 4. Goal Analytics
    goals = Goal.query.filter_by(user_id=user_id).all()
    goal_analytics_list = []
    completed_count = 0
    active_count = 0

    for g in goals:
        prog_pct = round((g.current_amount / g.target_amount) * 100, 1) if g.target_amount > 0 else 0.0
        rem_amt = max(0.0, g.target_amount - g.current_amount)

        if g.status == "Completed" or prog_pct >= 100.0:
            completed_count += 1
        else:
            active_count += 1

        goal_analytics_list.append({
            "goal": g,
            "prog_pct": prog_pct,
            "rem_amt": rem_amt
        })

    return render_template(
        "analytics.html",
        rebuilt_data=rebuilt_data,
        spending_analysis=spending_analysis,
        spending_periods_data=spending_periods_data,
        cash_flow_trend=cash_flow_trend,
        advanced_patterns=advanced_patterns,
        goal_expense_analytics=goal_expense_analytics,
        alerts=alerts,
        budget_analytics_list=budget_analytics_list,
        goal_analytics_list=goal_analytics_list,
        completed_count=completed_count,
        active_count=active_count,
        health_score=health_score,
        current_month_name=current_month_name,
        current_year=current_year,
        selected_month=rec_month,
        selected_year=rec_year,
        rec_month=rec_month,
        rec_year=rec_year,
        rec_budget_info=rec_budget_info,
        rec_rule_recommendations=rec_rule_recommendations,
        active_tab=request.args.get("active_tab", "overview")
    )
