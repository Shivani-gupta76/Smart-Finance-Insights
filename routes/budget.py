from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models.budget import Budget
from models.goal import Goal

budget = Blueprint("budget", __name__)


@budget.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():

    current_budget = Budget.query.filter_by(user_id=current_user.id).first()
    goals = Goal.query.filter_by(user_id=current_user.id).all()

    if request.method == "POST":

        monthly_budget = request.form.get("monthly_budget")
        month = request.form.get("month")
        year = request.form.get("year")
        goal_id_raw = request.form.get("goal_id")
        goal_id = int(goal_id_raw) if goal_id_raw and goal_id_raw.isdigit() else None

        if current_budget:
            current_budget.monthly_budget = monthly_budget
            current_budget.month = month
            current_budget.year = year
            current_budget.goal_id = goal_id

            flash("Budget updated successfully!", "success")

        else:
            new_budget = Budget(
                monthly_budget=monthly_budget,
                month=month,
                year=year,
                goal_id=goal_id,
                user_id=current_user.id
            )

            db.session.add(new_budget)

            flash("Budget added successfully!", "success")

        db.session.commit()

        return redirect(url_for("budget.budgets"))

    return render_template(
        "budgets.html",
        budget=current_budget,
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