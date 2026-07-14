from datetime import datetime
from app.extensions import db


class Workout(db.Model):

    __tablename__ = "workouts"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    workout_type = db.Column(db.String(100))

    duration = db.Column(db.Integer)

    calories_burned = db.Column(db.Integer)

    exercises = db.Column(db.Text)

    notes = db.Column(db.Text)

    date = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Workout {self.workout_type}>"