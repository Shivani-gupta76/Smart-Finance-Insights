from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from extensions import db
from models.expense import Expense
from models.account import Account
from models.goal import Goal
from datetime import datetime

expense = Blueprint(
    "expense",
    __name__
)


@expense.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses():

    accounts = Account.query.filter_by(
        user_id=current_user.id
    ).all()

    goals = Goal.query.filter_by(
        user_id=current_user.id
    ).all()

    if request.method == "POST":

        title = request.form.get("title")
        category = request.form.get("category")
        amount = float(request.form.get("amount"))
        payment_method = request.form.get("payment_method")
        account_id = int(request.form.get("account_id"))
        expense_date = request.form.get("expense_date")
        description = request.form.get("description")

        goal_id_val = request.form.get("goal_id")
        goal_id = None
        if goal_id_val and goal_id_val.strip() and goal_id_val != "none" and goal_id_val != "0":
            gid = int(goal_id_val)
            g_check = Goal.query.filter_by(id=gid, user_id=current_user.id).first()
            if g_check:
                goal_id = gid

        account = Account.query.filter_by(
            id=account_id,
            user_id=current_user.id
        ).first_or_404()

        # Deduct balance
        account.balance -= amount

        new_expense = Expense(
            title=title,
            category=category,
            amount=amount,
            payment_method=payment_method,
            account_id=account_id,
            expense_date=datetime.strptime(
                expense_date,
                "%Y-%m-%d"
            ).date(),
            description=description,
            user_id=current_user.id,
            goal_id=goal_id
        )

        db.session.add(new_expense)
        db.session.commit()

        return redirect(url_for("expense.expenses"))

    expenses_list = Expense.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Expense.expense_date.desc()
    ).all()

    return render_template(
        "expenses.html",
        expenses=expenses_list,
        accounts=accounts,
        goals=goals
    )


@expense.route("/expense/delete/<int:id>")
@login_required
def delete_expense(id):

    expense_obj = Expense.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    # Restore account balance
    expense_obj.account.balance += expense_obj.amount

    db.session.delete(expense_obj)
    db.session.commit()

    return redirect(url_for("expense.expenses"))


@expense.route("/expense/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_expense(id):

    expense_obj = Expense.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    accounts = Account.query.filter_by(
        user_id=current_user.id
    ).all()

    goals = Goal.query.filter_by(
        user_id=current_user.id
    ).all()

    if request.method == "POST":

        old_account = expense_obj.account
        old_amount = expense_obj.amount

        # Restore previous balance
        old_account.balance += old_amount

        new_account_id = int(request.form.get("account_id"))
        new_account = Account.query.filter_by(
            id=new_account_id,
            user_id=current_user.id
        ).first_or_404()

        new_amount = float(request.form.get("amount"))

        # Deduct from selected account
        new_account.balance -= new_amount

        goal_id_val = request.form.get("goal_id")
        goal_id = None
        if goal_id_val and goal_id_val.strip() and goal_id_val != "none" and goal_id_val != "0":
            gid = int(goal_id_val)
            g_check = Goal.query.filter_by(id=gid, user_id=current_user.id).first()
            if g_check:
                goal_id = gid

        expense_obj.title = request.form.get("title")
        expense_obj.category = request.form.get("category")
        expense_obj.amount = new_amount
        expense_obj.payment_method = request.form.get("payment_method")
        expense_obj.account_id = new_account_id
        expense_obj.expense_date = datetime.strptime(
            request.form.get("expense_date"),
            "%Y-%m-%d"
        ).date()
        expense_obj.description = request.form.get("description")
        expense_obj.goal_id = goal_id

        db.session.commit()
        
        return redirect(url_for("expense.expenses"))

    return render_template(
        "edit_expense.html",
        expense=expense_obj,
        accounts=accounts,
        goals=goals
    )
