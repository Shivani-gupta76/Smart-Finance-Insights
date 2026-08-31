from datetime import datetime
from extensions import db


class Account(db.Model):
    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)

    account_name = db.Column(
        db.String(100),
        nullable=False
    )

    account_type = db.Column(
        db.String(50),
        nullable=False
    )

    balance = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    description = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Relationship with Expense
    expenses = db.relationship(
    "Expense",
    back_populates="account"
)

    def __repr__(self):
        return f"<Account {self.account_name}>"