from app.extensions import db
from datetime import datetime


class DietPlan(db.Model):
    __tablename__ = "diet_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    meal_type = db.Column(db.String(50), nullable=False)
    meal_name = db.Column(db.String(200), nullable=False)

    calories = db.Column(db.Integer)
    protein = db.Column(db.Integer)
    carbs = db.Column(db.Integer)
    fat = db.Column(db.Integer)
    description = db.Column(db.Text)
    intake_time = db.Column(db.String(20)) # e.g., "08:00 AM" or "Morning"

    # Day of week for scheduling
    day_of_week = db.Column(db.String(20))  # Monday, Tuesday, etc.

    # Status tracking
    status = db.Column(db.String(20), default="Pending")
    completed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship("User", backref="diet_plans", lazy=True)

    # Method to mark as completed
    def mark_completed(self):
        self.status = "Completed"
        self.completed_at = datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "meal_type": self.meal_type,
            "meal_name": self.meal_name,
            "calories": self.calories,
            "description": self.description,
            "intake_time": self.intake_time,
            "day_of_week": self.day_of_week,
            "status": self.status
        }