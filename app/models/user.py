from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile_number = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), default="user")

    otp_code = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)

    age = db.Column(db.Integer)
    height = db.Column(db.Float)  # cm
    weight = db.Column(db.Float)  # kg

    gender = db.Column(db.String(10))
    activity_level = db.Column(db.String(20))

    notifications_enabled = db.Column(db.Boolean, default=True)
    preferred_units = db.Column(db.String(10), default="metric")
    profile_private = db.Column(db.Boolean, default=False)

    # ✅ FIXED: Use consistent field name
    profile_pic = db.Column(db.String(255), default="default.png")

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # =========================
    # PASSWORD FUNCTIONS
    # =========================
    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    # =========================
    # FITNESS CALCULATIONS
    # =========================
    def calculate_bmi(self):
        """Calculate Body Mass Index"""
        if not self.height or not self.weight:
            return None

        height_m = self.height / 100
        bmi = self.weight / (height_m ** 2)

        return round(bmi, 1)

    def bmi_category(self):
        """Return BMI Category"""
        bmi = self.calculate_bmi()

        if not bmi:
            return None

        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"

    def calculate_bmr(self):
        """Calculate Basal Metabolic Rate (Mifflin-St Jeor Equation)"""

        if not self.height or not self.weight or not self.age:
            return None

        if self.gender == "male":
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5

        elif self.gender == "female":
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161

        else:
            return None

        return round(bmr, 0)

    def calculate_tdee(self):
        """Calculate Total Daily Energy Expenditure"""

        bmr = self.calculate_bmr()

        if not bmr:
            return None

        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }

        multiplier = activity_multipliers.get(self.activity_level, 1.2)

        tdee = bmr * multiplier

        return round(tdee, 0)

    # =========================
    # PROFILE UTILITIES
    # =========================
    def get_profile_image(self):
        """Return profile image path"""
        if self.profile_pic and self.profile_pic != "default.png":
            return f"uploads/profiles/{self.profile_pic}"
        return "images/default.png"

    # =========================
    # REPRESENTATION
    # =========================
    def __repr__(self):
        return f"<User {self.email}>"