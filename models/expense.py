from datetime import datetime
from extensions import db


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(100),
        nullable=False
    )

    category = db.Column(
        db.String(50),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    payment_method = db.Column(
        db.String(30),
        nullable=False
    )

    # Account used for this expense
    account_id = db.Column(
        db.Integer,
        db.ForeignKey("accounts.id"),
        nullable=False
    )

    expense_date = db.Column(
        db.Date,
        nullable=False,
        index=True
    )

    description = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

# Optional relationship with Financial Goal
goal_id = db.Column(
    db.Integer,
    db.ForeignKey("goals.id"),
    nullable=True,
    index=True
)

# Relationship with Account
account = db.relationship(
    "Account",
    back_populates="expenses"
)

# Relationship with Goal
goal = db.relationship(
    "Goal",
    back_populates="expenses"
)

def __repr__(self):
    return f"<Expense {self.title}>"