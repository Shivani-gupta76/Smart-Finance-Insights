from datetime import datetime

from extensions import db


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    goal_name = db.Column(
        db.String(100),
        nullable=False
    )

    goal_type = db.Column(
        db.String(50),
        nullable=False
    )

    target_amount = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    current_amount = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    target_date = db.Column(
        db.Date,
        nullable=False,
        index=True
    )

    category = db.Column(
        db.String(50),
        nullable=False
    )

    priority = db.Column(
        db.String(20),
        nullable=False,
        default="Medium"
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="In Progress"
    )

    notes = db.Column(
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

    # Relationship with Expenses
    expenses = db.relationship(
        "Expense",
        back_populates="goal",
        lazy=True
    )
    
    # Relationship with Expenses
    expenses = db.relationship(
        "Expense",
        back_populates="goal",
        lazy=True
    )
    
    def __repr__(self):
        return f"<Goal {self.goal_name}>"
