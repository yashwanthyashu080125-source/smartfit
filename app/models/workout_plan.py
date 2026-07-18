from app.extensions import db
from datetime import datetime
import typing


class WorkoutPlan(db.Model):
    __tablename__ = "workout_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    workout_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)  # in minutes
    difficulty = db.Column(db.String(20))  # Beginner, Intermediate, Advanced

    # ✅ ADDED: Day of week for scheduling
    day_of_week = db.Column(db.String(20))  # Monday, Tuesday, etc.

    # ✅ Status tracking
    status = db.Column(db.String(20), default="Pending")
    completed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ ADDED: Photo for the workout
    image_filename = db.Column(db.String(255))

    # ✅ ADDED: Estimated calories to burn
    calories_to_burn = db.Column(db.Integer, default=0)

    # ✅ Relationship
    user = db.relationship("User", backref="workout_plans", lazy=True)

    def __init__(self, **kwargs: typing.Any) -> None:
        super(WorkoutPlan, self).__init__(**kwargs)


    # ✅ Method to mark as completed
    def mark_completed(self):
        self.status = "Completed"
        self.completed_at = datetime.utcnow()