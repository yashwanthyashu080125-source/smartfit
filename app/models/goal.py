from app.extensions import db
from datetime import datetime


class Goal(db.Model):
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_value = db.Column(db.Float, nullable=True)
    current_value = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(20), nullable=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    target_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('goals', lazy=True))

    def __repr__(self):
        return f'<Goal {self.title} - {self.goal_type}>'

    def calculate_progress(self):
        """Smart Sync: Calculate goal progress percentage based on actual activity history"""
        from app.models.workout import Workout
        from app.models.nutrition import NutritionLog
        from app.models.workout_plan import WorkoutPlan
        from app.models.diet_plan import DietPlan

        if not self.target_value or self.target_value == 0:
            return 0

        # 1. Weight Loss / Muscle Gain (Synced with User Profile)
        if self.goal_type in ['weight_loss', 'muscle_gain']:
            current_weight = self.user.weight if self.user.weight else 0
            if current_weight == 0: return 0
            
            if self.goal_type == 'weight_loss':
                # Starting weight is assumed to be the weight when the goal was created
                # For simplicity, if current > target, we calculate how far we've come
                # If current <= target, it's 100%
                if current_weight <= self.target_value:
                    return 100
                # We need a starting point. Let's assume the user's weight was at least 
                # something higher. If we don't have a starting weight, we use a simple ratio.
                # A better way is to track progress relative to target.
                progress = (self.target_value / current_weight) * 100
                return min(max(progress, 0), 100)
            else: # muscle_gain
                if current_weight >= self.target_value:
                    return 100
                progress = (current_weight / self.target_value) * 100
                return min(max(progress, 0), 100)

        # 2. Fitness (Synced with Workout Logs - Calories)
        elif self.goal_type == 'fitness':
            # Sum calories burned in workouts since start_date
            total_burned = db.session.query(db.func.sum(Workout.calories_burned)).filter(
                Workout.user_id == self.user_id,
                Workout.date >= self.start_date
            ).scalar() or 0
            
            # Also include completed workout plans
            completed_plans_cals = db.session.query(db.func.sum(WorkoutPlan.calories_to_burn)).filter(
                WorkoutPlan.user_id == self.user_id,
                WorkoutPlan.status == 'Completed',
                WorkoutPlan.completed_at != None,
                WorkoutPlan.completed_at >= self.start_date
            ).scalar() or 0
            
            total_burned += completed_plans_cals
            progress = (total_burned / self.target_value) * 100
            return min(max(progress, 0), 100)

        # 3. Nutrition (Synced with Diet Plans / Nutrition Logs)
        elif self.goal_type == 'nutrition':
            # Option A: Count completed meals
            completed_meals = DietPlan.query.filter(
                DietPlan.user_id == self.user_id,
                DietPlan.status == 'Completed',
                DietPlan.completed_at != None,
                DietPlan.completed_at >= self.start_date
            ).count()
            
            progress = (completed_meals / self.target_value) * 100
            return min(max(progress, 0), 100)

        return 0

    def get_current_stats(self):
        """Helper to get the current raw value being tracked"""
        from app.models.workout import Workout
        from app.models.diet_plan import DietPlan

        if self.goal_type in ['weight_loss', 'muscle_gain']:
            return self.user.weight or 0
        elif self.goal_type == 'fitness':
            total_burned = db.session.query(db.func.sum(Workout.calories_burned)).filter(
                Workout.user_id == self.user_id,
                Workout.date >= self.start_date
            ).scalar() or 0
            return total_burned
        elif self.goal_type == 'nutrition':
            return DietPlan.query.filter(
                DietPlan.user_id == self.user_id,
                DietPlan.status == 'Completed',
                DietPlan.completed_at >= self.start_date
            ).count()
        return 0