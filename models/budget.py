from extensions import db
from datetime import datetime


class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)

    monthly_budget = db.Column(db.Float, nullable=False)

    month = db.Column(db.String(20), nullable=False)

    year = db.Column(db.Integer, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    goal_id = db.Column(
        db.Integer,
        db.ForeignKey("goals.id"),
        nullable=True
    )

    goal = db.relationship(
        "Goal",
        backref=db.backref("budgets", lazy=True)
    )