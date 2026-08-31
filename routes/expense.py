from flask import Blueprint, render_template, request, redirect, url_for, flash
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
        amount_raw = request.form.get("amount")
        payment_method = request.form.get("payment_method")
        account_id_raw = request.form.get("account_id")
        expense_date_raw = request.form.get("expense_date")
        description = request.form.get("description")

        if not title or not category or not amount_raw or not account_id_raw or not expense_date_raw or not payment_method:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("expense.expenses"))

        try:
            amount = float(amount_raw)
            if amount <= 0:
                flash("Expense amount must be greater than zero.", "danger")
                return redirect(url_for("expense.expenses"))
        except (ValueError, TypeError):
            flash("Invalid expense amount format.", "danger")
            return redirect(url_for("expense.expenses"))

        try:
            account_id = int(account_id_raw)
        except (ValueError, TypeError):
            flash("Invalid account selected.", "danger")
            return redirect(url_for("expense.expenses"))

        try:
            exp_date = datetime.strptime(expense_date_raw, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            flash("Invalid expense date format.", "danger")
            return redirect(url_for("expense.expenses"))

        goal_id_val = request.form.get("goal_id")
        goal_id = None
        if goal_id_val and goal_id_val.strip() and goal_id_val != "none" and goal_id_val != "0":
            try:
                gid = int(goal_id_val)
                g_check = Goal.query.filter_by(id=gid, user_id=current_user.id).first()
                if g_check:
                    goal_id = gid
            except (ValueError, TypeError):
                goal_id = None

       

        account = Account.query.filter_by(
            id=account_id,
            user_id=current_user.id
        ).first()

        if not account:
            flash("Selected account not found or access denied.", "danger")
            return redirect(url_for("expense.expenses"))

        # Deduct balance
        account.balance -= amount

        new_expense = Expense(
            title=title,
            category=category,
            amount=amount,
            payment_method=payment_method,
            account_id=account_id,
            expense_date=exp_date,
            description=description,
            user_id=current_user.id,
            goal_id=goal_id
        )

        db.session.add(new_expense)
        db.session.commit()
        flash("Expense recorded successfully.", "success")

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

    if expense_obj.account:
        expense_obj.account.balance += expense_obj.amount

    

    db.session.delete(expense_obj)
    db.session.commit()
    flash("Expense deleted successfully.", "success")

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


        amount_raw = request.form.get("amount")
        account_id_raw = request.form.get("account_id")
        expense_date_raw = request.form.get("expense_date")

        try:
            new_amount = float(amount_raw)
            if new_amount <= 0:
                flash("Expense amount must be greater than zero.", "danger")
                return redirect(url_for("expense.edit_expense", id=id))
        except (ValueError, TypeError):
            flash("Invalid expense amount format.", "danger")
            return redirect(url_for("expense.edit_expense", id=id))

        try:
            new_account_id = int(account_id_raw)
        except (ValueError, TypeError):
            flash("Invalid account selected.", "danger")
            return redirect(url_for("expense.edit_expense", id=id))

        try:
            exp_date = datetime.strptime(expense_date_raw, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            flash("Invalid expense date format.", "danger")
            return redirect(url_for("expense.edit_expense", id=id))


        old_account = expense_obj.account
        old_amount = expense_obj.amount

        # Restore previous balance
        if old_account:
            old_account.balance += old_amount

        new_account = Account.query.filter_by(
            id=new_account_id,
            user_id=current_user.id
        ).first()

        if not new_account:
            flash("Selected account not found or access denied.", "danger")
            return redirect(url_for("expense.edit_expense", id=id))

                # Deduct from selected account
        new_account.balance -= new_amount

        goal_id_val = request.form.get("goal_id")
        goal_id = None

        if goal_id_val and goal_id_val.strip() and goal_id_val != "none" and goal_id_val != "0":
            try:
                gid = int(goal_id_val)
                g_check = Goal.query.filter_by(
                    id=gid,
                    user_id=current_user.id
                ).first()

                if g_check:
                    goal_id = gid

            except (ValueError, TypeError):
                goal_id = None

        expense_obj.title = request.form.get("title")
        expense_obj.category = request.form.get("category")
        expense_obj.amount = new_amount
        expense_obj.payment_method = request.form.get("payment_method")
        expense_obj.account_id = new_account_id
        expense_obj.expense_date = exp_date
        expense_obj.description = request.form.get("description")
        expense_obj.goal_id = goal_id

        db.session.commit()
        flash("Expense updated successfully.", "success")
        return redirect(url_for("expense.expenses"))


