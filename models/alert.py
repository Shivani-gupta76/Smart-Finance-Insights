from datetime import datetime
from extensions import db


class FinancialAlert(db.Model):
    __tablename__ = "financial_alerts"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    alert_type = db.Column(
        db.String(50),
        nullable=False
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    severity = db.Column(
        db.String(20),
        nullable=False,
        default="warning"
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref=db.backref("alerts", lazy=True, cascade="all, delete-orphan")
    )

    def __repr__(self):
        return f"<FinancialAlert {self.title}>"
