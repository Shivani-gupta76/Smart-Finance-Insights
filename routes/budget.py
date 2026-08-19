from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models.budget import Budget

budget = Blueprint("budget", __name__)


@budget.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():

    current_budget = Budget.query.filter_by(user_id=current_user.id).first()

    if request.method == "POST":

        monthly_budget = request.form.get("monthly_budget")
        month = request.form.get("month")
        year = request.form.get("year")

        if current_budget:
            current_budget.monthly_budget = monthly_budget
            current_budget.month = month
            current_budget.year = year

            flash("Budget updated successfully!", "success")

        else:
            new_budget = Budget(
                monthly_budget=monthly_budget,
                month=month,
                year=year,
                user_id=current_user.id
            )

            db.session.add(new_budget)

            flash("Budget added successfully!", "success")

        db.session.commit()

        return redirect(url_for("budget.budgets"))

    return render_template(
        "budgets.html",
        budget=current_budget
    )