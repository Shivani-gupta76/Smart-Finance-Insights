from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models.budget import Budget
from models.goal import Goal
from models.expense import Expense

budget = Blueprint("budget", __name__)

MONTH_NAME_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
}


def get_last_day_of_month(dt_start):
    """
    Returns the last day of the month for a given 1st-of-month date.
    """
    if dt_start.month == 12:
        next_month = date(dt_start.year + 1, 1, 1)
    else:
        next_month = date(dt_start.year, dt_start.month + 1, 1)
    return next_month - timedelta(days=1)


@budget.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():
    all_budgets = Budget.query.filter_by(user_id=current_user.id).all()
    all_budgets.sort(
        key=lambda b: (b.year, MONTH_NAME_MAP.get(b.month.strip().lower(), 0)),
        reverse=True
    )
    
    req_month = request.args.get("month")
    req_year = request.args.get("year", type=int)

    if req_month and req_year:
        current_budget = Budget.query.filter(
            Budget.user_id == current_user.id,
            db.func.lower(Budget.month) == req_month.lower(),
            Budget.year == req_year
        ).first()
    else:
        current_budget = all_budgets[0] if all_budgets else None

    goals = Goal.query.filter_by(user_id=current_user.id).all()

    if request.method == "POST":

        monthly_budget_raw = request.form.get("monthly_budget")
        month = request.form.get("month")
        year_raw = request.form.get("year")
        goal_id_raw = request.form.get("goal_id")

        if not monthly_budget_raw or not month or not year_raw:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("budget.budgets"))

        try:
            monthly_budget = float(monthly_budget_raw)
            if monthly_budget <= 0:
                flash("Monthly budget must be greater than zero.", "danger")
                return redirect(url_for("budget.budgets"))
        except (ValueError, TypeError):
            flash("Invalid monthly budget amount format.", "danger")
            return redirect(url_for("budget.budgets"))

        try:
            year = int(year_raw)
        except (ValueError, TypeError):
            flash("Invalid year format.", "danger")
            return redirect(url_for("budget.budgets"))

        goal_id = int(goal_id_raw) if goal_id_raw and goal_id_raw.isdigit() else None

        existing_budget = Budget.query.filter(
            Budget.user_id == current_user.id,
            db.func.lower(Budget.month) == month.strip().lower(),
            Budget.year == year
        ).first()

        if existing_budget:
            existing_budget.monthly_budget = monthly_budget
            existing_budget.goal_id = goal_id
            flash(f"Budget for {month} {year} updated successfully!", "success")
        else:
            new_budget = Budget(
                monthly_budget=monthly_budget,
                month=month.strip(),
                year=year,
                goal_id=goal_id,
                user_id=current_user.id
            )
            db.session.add(new_budget)
            flash(f"Budget for {month} {year} added successfully!", "success")

        db.session.commit()
        return redirect(url_for("budget.budgets", month=month, year=year))

    today = date.today()
    budget_history = []

    for b in all_budgets:
        month_str = b.month.strip()
        month_num = MONTH_NAME_MAP.get(month_str.lower(), 1)
        start_date = date(b.year, month_num, 1)
        last_day = get_last_day_of_month(start_date)

        if b.year == today.year and month_num == today.month:
            end_date = min(today, last_day)
        else:
            end_date = last_day

        month_expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        ).all()

        spent_amount = sum(e.amount for e in month_expenses)

        if b.monthly_budget > 0:
            usage_pct = (spent_amount / b.monthly_budget) * 100.0
        else:
            usage_pct = 0.0

        remaining = b.monthly_budget - spent_amount

        if usage_pct < 80.0:
            status = "Healthy"
            status_class = "status-healthy"
        elif usage_pct <= 100.0:
            status = "On Track"
            status_class = "status-ontrack"
        else:
            status = "Over Budget"
            status_class = "status-overbudget"

        budget_history.append({
            "id": b.id,
            "month": month_str,
            "year": b.year,
            "monthly_budget": b.monthly_budget,
            "goal": b.goal.goal_name if b.goal else None,
            "spent_amount": spent_amount,
            "usage_pct": round(usage_pct, 1),
            "remaining": remaining,
            "status": status,
            "status_class": status_class
        })

    return render_template(
        "budgets.html",
        budget=current_budget,
        all_budgets=all_budgets,
        budget_history=budget_history,
        goals=goals
    )


@budget.route("/budgets/delete/<int:id>", methods=["POST", "GET"])
@login_required
def delete_budget(id):
    target_budget = Budget.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(target_budget)
    db.session.commit()
    flash("Budget deleted successfully!", "success")
    return redirect(url_for("budget.budgets"))