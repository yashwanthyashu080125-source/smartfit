from app.extensions import db
from datetime import datetime


class NutritionLog(db.Model):

    __tablename__ = "nutrition_logs"

    id = db.Column(db.Integer, primary_key=True)

    # ============================
    # USER RELATION
    # ============================

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    user = db.relationship(
        'User',
        backref=db.backref('nutrition_logs', lazy=True)
    )

    # ============================
    # MEAL INFORMATION
    # ============================

    meal_name = db.Column(
        db.String(150)
    )

    meal_type = db.Column(
        db.String(50)
    )

    # NEW (for uploaded image)
    meal_image = db.Column(
        db.String(255)
    )

    # ============================
    # NUTRITION VALUES
    # ============================

    calories = db.Column(
        db.Float,
        default=0
    )

    protein = db.Column(
        db.Float,
        default=0
    )

    carbohydrates = db.Column(
        db.Float,
        default=0
    )

    fat = db.Column(
        db.Float,
        default=0
    )

    fiber = db.Column(
        db.Float,
        default=0
    )

    # ============================
    # OPTIONAL NOTES
    # ============================

    notes = db.Column(
        db.Text
    )

    # ============================
    # TIMESTAMPS
    # ============================

    date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # ============================
    # INITIALIZATION
    # ============================

    def __init__(self, **kwargs):
        super(NutritionLog, self).__init__(**kwargs)

    # ============================
    # STRING REPRESENTATION
    # ============================

    def __repr__(self):
        return f"<NutritionLog {self.meal_name} | {self.calories} kcal>"