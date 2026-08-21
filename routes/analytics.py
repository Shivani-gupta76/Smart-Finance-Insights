from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required, current_user

from extensions import db
from models.account import Account

account = Blueprint("account", __name__)


# View + Add Account

@account.route("/accounts", methods=["GET", "POST"])
@login_required
def accounts():

    if request.method == "POST":

        account_name = request.form.get("account_name")
        account_type = request.form.get("account_type")
        balance = request.form.get("balance")
        description = request.form.get("description")

        new_account = Account(
            account_name=account_name,
            account_type=account_type,
            balance=float(balance),
            description=description,
            user_id=current_user.id
        )

        db.session.add(new_account)
        db.session.commit()

        flash("Account added successfully!", "success")

        return redirect(url_for("account.accounts"))

    accounts = Account.query.filter_by(
        user_id=current_user.id
    ).order_by(Account.created_at.desc()).all()

    return render_template(
        "accounts.html",
        accounts=accounts
    )



# Edit Account

@account.route("/accounts/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_account(id):

    account_data = Account.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        account_data.account_name = request.form.get("account_name")
        account_data.account_type = request.form.get("account_type")
        account_data.balance = float(request.form.get("balance"))
        account_data.description = request.form.get("description")

        db.session.commit()

        flash("Account updated successfully!", "success")

        return redirect(url_for("account.accounts"))

    return render_template(
        "edit_account.html",
        account=account_data
    )



# Delete Account

@account.route("/accounts/delete/<int:id>")
@login_required
def delete_account(id):

    account_data = Account.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(account_data)
    db.session.commit()

    flash("Account deleted successfully!", "success")

    return redirect(url_for("account.accounts"))
