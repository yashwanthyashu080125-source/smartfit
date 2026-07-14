from datetime import datetime
from app.extensions import db


class WorkoutSet(db.Model):
    """Stores structured per-exercise set data logged by users."""

    __tablename__ = "workout_sets"

    id = db.Column(db.Integer, primary_key=True)

    # Link to the user and the parent workout log
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    workout_id = db.Column(db.Integer, db.ForeignKey("workouts.id"), nullable=True)

    # Structured exercise data (MacroFactor-style)
    exercise_name = db.Column(db.String(150), nullable=False)
    sets = db.Column(db.Integer, default=1)
    reps = db.Column(db.Integer, default=0)
    weight_kg = db.Column(db.Float, default=0.0)
    rpe = db.Column(db.Integer, default=5)  # Rate of Perceived Exertion (1–10)

    # Volume = sets * reps * weight_kg (calculated field for analytics)
    @property
    def volume(self):
        return (self.sets or 0) * (self.reps or 0) * (self.weight_kg or 0)

    logged_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User", backref="workout_sets", lazy=True)
    workout = db.relationship("Workout", backref="sets", lazy=True)

    def __repr__(self):
        return f"<WorkoutSet {self.exercise_name} {self.sets}x{self.reps}@{self.weight_kg}kg>"
