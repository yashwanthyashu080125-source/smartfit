from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from collections import Counter
import os
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.user import User
from app.models.workout import Workout
from app.models.nutrition import NutritionLog
from app.models.goal import Goal
from app.models.workout_plan import WorkoutPlan
from app.models.diet_plan import DietPlan
from app.models.activity import Activity
from app.models.support import SupportTicket
from app.models.notification import Notification
from app.models.workout_set import WorkoutSet
from app.services.food_ai import detect_food, get_food_nutrition
from app.services.meal_recommendation import recommend_meals

# ✅ FIXED: Use __name__ instead of 'name'
dashboard = Blueprint('dashboard', __name__)

from sqlalchemy import text

@dashboard.route('/fix-db-schema')
def fix_db_schema():
    try:
        db.session.execute(text("ALTER TABLE workout_plans ADD COLUMN completed_at DATETIME NULL"))
        db.session.commit()
        return "<h3>✅ Success!</h3><p>The <code>completed_at</code> column has been added to the <code>workout_plans</code> table.</p><p><a href='/dashboard/'>Return to Dashboard</a></p>"
    except Exception as e:
        db.session.rollback()
        return f"<h3>⚠️ Info</h3><p>The column might already exist or another error occurred: {str(e)}</p><p><a href='/dashboard/'>Return to Dashboard</a></p>"


@dashboard.route('/fix-schema-sets')
def fix_schema_sets():
    """One-time migration: creates all missing tables (including workout_sets) using SQLAlchemy."""
    try:
        # This will create all tables defined in models that don't exist yet
        db.create_all()
        db.session.commit()
        return "<h3>✅ Tables created successfully!</h3><p>The <code>workout_sets</code> table (and any others) are now ready.</p><p><a href='/dashboard/performance'>Go to Performance</a></p>"
    except Exception as e:
        db.session.rollback()
        return f"<h3>⚠️ Error</h3><p>{str(e)}</p><p><a href='/dashboard/'>Return to Dashboard</a></p>"


# ==============================
# USER ACCESS CONTROL
# ==============================
def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)

    return decorated_function


# ==============================
# MAIN DASHBOARD
# ==============================
@dashboard.route('/')
@user_required
def index():
    user = current_user
    week_ago = datetime.utcnow() - timedelta(days=7)

    workouts_this_week = Workout.query.filter(
        Workout.user_id == user.id,
        Workout.date >= week_ago
    ).count()

    calories_burned = db.session.query(
        db.func.sum(Workout.calories_burned)
    ).filter(
        Workout.user_id == user.id,
        Workout.date >= week_ago
    ).scalar() or 0

    bmi = user.calculate_bmi()
    today = datetime.utcnow().date()

    today_nutrition = NutritionLog.query.filter(
        NutritionLog.user_id == user.id,
        db.func.date(NutritionLog.date) == today
    ).all()

    today_calories = sum(log.calories for log in today_nutrition) if today_nutrition else 0

    today_day_str = today.strftime('%A')
    threshold = datetime.utcnow() - timedelta(minutes=10)
    today_workout_plans = WorkoutPlan.query.filter(
        WorkoutPlan.user_id == user.id,
        WorkoutPlan.day_of_week == today_day_str,
        db.or_(
            WorkoutPlan.status != 'Completed',
            WorkoutPlan.completed_at >= threshold
        )
    ).all()
    
    today_diet_plans = DietPlan.query.filter(
        DietPlan.user_id == user.id,
        DietPlan.day_of_week == today_day_str,
        db.or_(
            DietPlan.status != 'Completed',
            DietPlan.completed_at >= threshold
        )
    ).all()

    workout_plans = WorkoutPlan.query.filter(
        WorkoutPlan.user_id == user.id,
        db.or_(
            WorkoutPlan.status != 'Completed',
            WorkoutPlan.completed_at >= threshold
        )
    ).all()
    
    diet_plans = DietPlan.query.filter(
        DietPlan.user_id == user.id,
        db.or_(
            DietPlan.status != 'Completed',
            DietPlan.completed_at >= threshold
        )
    ).all()


    return render_template(
        'dashboard/index.html',
        user=user,
        bmi=bmi,
        workouts_this_week=workouts_this_week,
        calories_burned=calories_burned,
        today_calories=today_calories,
        today_workout_plans=today_workout_plans,
        today_diet_plans=today_diet_plans,
        today_day_str=today_day_str,
        workout_plans=workout_plans,
        diet_plans=diet_plans
    )


# ==============================
# ANALYTICS - FIXED
# ==============================
@dashboard.route('/analytics')
@login_required
def analytics():
    workouts = Workout.query.filter_by(user_id=current_user.id).all()
    nutrition_logs = NutritionLog.query.filter_by(user_id=current_user.id).all()

    # Workout data
    labels = []
    calories = []
    duration = []

    for w in workouts:
        labels.append(w.date.strftime("%Y-%m-%d") if w.date else "Unknown")
        calories.append(w.calories_burned or 0)
        duration.append(w.duration or 0)

    # Nutrition data
    food_labels = []
    food_calories = []
    nutrition_protein = []
    nutrition_carbs = []
    nutrition_fat = []

    for n in nutrition_logs:
        food_labels.append(n.meal_name or 'Unknown')
        food_calories.append(n.calories or 0)
        nutrition_protein.append(n.protein or 0)
        nutrition_carbs.append(n.carbohydrates or 0)
        nutrition_fat.append(n.fat or 0)

    # Daily tracking
    daily_data = {}

    # Process workouts
    for workout in workouts:
        day = workout.date.strftime("%Y-%m-%d") if workout.date else "Unknown"
        if day not in daily_data:
            daily_data[day] = {'burned': 0, 'consumed': 0}
        daily_data[day]['burned'] += workout.calories_burned or 0

    # Process nutrition
    for log in nutrition_logs:
        day = log.date.strftime("%Y-%m-%d") if log.date else "Unknown"
        if day not in daily_data:
            daily_data[day] = {'burned': 0, 'consumed': 0}
        daily_data[day]['consumed'] += log.calories or 0

    # Sort by date
    sorted_days = sorted(daily_data.keys())
    daily_labels = sorted_days
    daily_burned = [daily_data[day]['burned'] for day in sorted_days]
    daily_consumed = [daily_data[day]['consumed'] for day in sorted_days]

    # Calculate metrics
    total_calories = sum(calories) if calories else 0
    total_consumed = sum(food_calories) if food_calories else 0
    net_calories = total_calories - total_consumed
    total_workouts = len(workouts)
    total_duration = sum(duration) if duration else 0
    avg_duration = int(total_duration / total_workouts) if total_workouts > 0 else 0

    # Sleep tracking data
    from app.models.sleep import SleepLog
    sleep_logs = SleepLog.query.filter_by(user_id=current_user.id).order_by(SleepLog.date.asc()).all()
    sleep_labels = [log.date.strftime('%b %d') for log in sleep_logs][-7:]
    sleep_data = [log.hours for log in sleep_logs][-7:]

    # ── NEW: Weekly Training Volume (from WorkoutSet) ──────────────────────────
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    workout_sets = WorkoutSet.query.filter(
        WorkoutSet.user_id == current_user.id,
        WorkoutSet.logged_at >= thirty_days_ago
    ).all()

    volume_by_day = {}
    for ws in workout_sets:
        day = ws.logged_at.strftime("%b %d")
        volume_by_day[day] = volume_by_day.get(day, 0) + ws.volume

    # Keep last 30 days sorted
    volume_labels = sorted(volume_by_day.keys(),
                           key=lambda d: datetime.strptime(d + f" {datetime.utcnow().year}", "%b %d %Y"))
    volume_data = [round(volume_by_day[d], 1) for d in volume_labels]

    # ── NEW: Workout Type Distribution ─────────────────────────────────────────
    type_counts_raw = Counter(w.workout_type for w in workouts if w.workout_type)
    type_labels = list(type_counts_raw.keys())
    type_counts = list(type_counts_raw.values())

    # ── NEW: RPE Trend (last 14 sessions) ─────────────────────────────────────
    recent_sets = WorkoutSet.query.filter_by(user_id=current_user.id)\
        .order_by(WorkoutSet.logged_at.asc()).limit(14).all()
    rpe_labels = [ws.logged_at.strftime("%b %d") for ws in recent_sets]
    rpe_data   = [ws.rpe for ws in recent_sets]

    return render_template(
        'dashboard/analytics.html',
        total_calories=total_calories,
        total_consumed=total_consumed,
        net_calories=net_calories,
        total_workouts=total_workouts,
        total_duration=total_duration,
        avg_duration=avg_duration,
        labels=labels,
        calories=calories,
        duration=duration,
        nutrition_protein=nutrition_protein,
        nutrition_carbs=nutrition_carbs,
        nutrition_fat=nutrition_fat,
        daily_labels=daily_labels,
        daily_burned=daily_burned,
        daily_consumed=daily_consumed,
        calories_change=0,
        workouts_change=0,
        # New MacroFactor-style data
        volume_labels=volume_labels,
        volume_data=volume_data,
        type_labels=type_labels,
        type_counts=type_counts,
        rpe_labels=rpe_labels,
        rpe_data=rpe_data,
        sleep_labels=sleep_labels,
        sleep_data=sleep_data
    )


# ==============================
# PERFORMANCE
# ==============================
@dashboard.route('/performance')
@login_required
def performance():
    workouts = Workout.query.filter_by(user_id=current_user.id).all()

    total_workouts = len(workouts)
    total_calories = sum(w.calories_burned or 0 for w in workouts)
    total_duration = sum(w.duration or 0 for w in workouts)

    dates = []
    calories = []
    duration = []

    for w in workouts:
        dates.append(w.date.strftime("%Y-%m-%d") if w.date else "Unknown")
        calories.append(w.calories_burned or 0)
        duration.append(w.duration or 0)

    # Workout Streak
    workout_dates = sorted([w.date for w in workouts if w.date])
    streak = 0

    if workout_dates:
        current = workout_dates[-1]
        for d in reversed(workout_dates):
            if (current - d).days <= 1:
                streak += 1
                current = d
            else:
                break

    # Best Day
    days = [w.date.strftime("%A") for w in workouts if w.date]
    best_day = Counter(days).most_common(1)[0][0] if days else "N/A"

    # Average Calories
    avg_calories = int(total_calories / total_workouts) if total_workouts > 0 else 0

    # Admin Assigned Workout Plan
    threshold = datetime.utcnow() - timedelta(minutes=10)
    workout_plans = WorkoutPlan.query.filter(
        WorkoutPlan.user_id == current_user.id,
        db.or_(
            WorkoutPlan.status != 'Completed',
            WorkoutPlan.completed_at >= threshold
        )
    ).all()

    # Workout Recommendations
    goal = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.start_date.desc()).first()
    goal_type = goal.goal_type if goal else None

    recommended_workouts = []
    if goal_type == "Weight Loss":
        recommended_workouts = [{"name": "HIIT Cardio", "duration": 30}, {"name": "Running", "duration": 20}]
    elif goal_type == "Muscle Gain":
        recommended_workouts = [{"name": "Strength Training", "duration": 45},
                                {"name": "Weight Lifting", "duration": 40}]
    else:
        recommended_workouts = [{"name": "Walking", "duration": 20}, {"name": "Yoga", "duration": 30}]

    # Fetch last 10 structured sets for "last session" display
    recent_sets = WorkoutSet.query.filter_by(user_id=current_user.id)\
        .order_by(WorkoutSet.logged_at.desc()).limit(10).all()

    # Weekly volume total
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_sets = WorkoutSet.query.filter(
        WorkoutSet.user_id == current_user.id,
        WorkoutSet.logged_at >= week_ago
    ).all()
    weekly_volume = sum(ws.volume for ws in weekly_sets)

    return render_template(
        "dashboard/performance.html",
        recommended_workouts=recommended_workouts,
        workouts=workouts,
        total_workouts=total_workouts,
        total_calories=total_calories,
        total_duration=total_duration,
        dates=dates,
        calories=calories,
        duration=duration,
        streak=streak,
        best_day=best_day,
        avg_calories=avg_calories,
        workout_plans=workout_plans,
        recent_sets=recent_sets,
        weekly_volume=weekly_volume
    )


# ==============================
# COMPLETE WORKOUT
# ==============================
@dashboard.route('/complete_workout/<int:id>')
@user_required
def complete_workout(id):
    workout = WorkoutPlan.query.get_or_404(id)
    if workout.user_id == current_user.id:
        workout.mark_completed()
        db.session.commit()
        flash("Workout completed!", "success")
    return redirect(url_for('dashboard.performance'))


# ==============================
# SKIP WORKOUT (NEW)
# ==============================
@dashboard.route('/skip_workout/<int:id>')
@user_required
def skip_workout(id):
    workout = WorkoutPlan.query.get_or_404(id)
    if workout.user_id == current_user.id:
        workout.status = "Skipped"
        db.session.commit()
        flash("Workout marked as skipped.", "info")
    return redirect(url_for('dashboard.performance'))


# ==============================
# ADD WORKOUT
# ==============================
@dashboard.route('/add-workout', methods=['POST'])
@user_required
def add_workout():
    workout = Workout(
        user_id=current_user.id,
        workout_type=request.form.get("workout_type"),
        duration=request.form.get("duration", type=int),
        calories_burned=request.form.get("calories", type=int),
        exercises=request.form.get("exercises"),
        notes=request.form.get("notes"),
        date=datetime.utcnow()
    )
    db.session.add(workout)
    db.session.flush()  # Get the workout.id before committing

    # Save structured set data if provided
    exercise_name = request.form.get("exercise_name", "").strip()
    if exercise_name:
        workout_set = WorkoutSet(
            user_id=current_user.id,
            workout_id=workout.id,
            exercise_name=exercise_name,
            sets=request.form.get("sets", type=int) or 1,
            reps=request.form.get("reps", type=int) or 0,
            weight_kg=request.form.get("weight_kg", type=float) or 0.0,
            rpe=request.form.get("rpe", type=int) or 5,
            logged_at=datetime.utcnow()
        )
        db.session.add(workout_set)

    db.session.commit()
    flash("Workout logged successfully!", "success")
    return redirect(url_for('dashboard.performance'))


# ==============================
# NUTRITION PAGE
# ==============================
@dashboard.route('/nutrition')
@user_required
def nutrition():
    threshold = datetime.utcnow() - timedelta(minutes=10)
    meals = DietPlan.query.filter(
        DietPlan.user_id == current_user.id,
        db.or_(
            DietPlan.status != 'Completed',
            DietPlan.completed_at >= threshold
        )
    ).order_by(DietPlan.day_of_week).all()
    
    # Group by status for tabs
    pending_meals = [m for m in meals if m.status == 'Pending']
    completed_meals = [m for m in meals if m.status == 'Completed']
    skipped_meals = [m for m in meals if m.status == 'Skipped']

    # Group pending by day for the "Today/Upcoming" view
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    grouped_pending = {day: [] for day in days_order}
    for meal in pending_meals:
        if meal.day_of_week in grouped_pending:
            grouped_pending[meal.day_of_week].append(meal.to_dict())
    grouped_pending = {day: m for day, m in grouped_pending.items() if m}

    nutrition_logs = NutritionLog.query.filter_by(
        user_id=current_user.id
    ).order_by(NutritionLog.date.desc()).all()

    return render_template(
        'dashboard/nutrition.html',
        pending_meals=pending_meals,
        completed_meals=completed_meals,
        skipped_meals=skipped_meals,
        grouped_pending=grouped_pending,
        nutrition_logs=nutrition_logs
    )


# ==============================
# COMPLETE MEAL
# ==============================
@dashboard.route('/complete_meal/<int:id>')
@user_required
def complete_meal(id):
    meal = DietPlan.query.get_or_404(id)
    if meal.user_id == current_user.id:
        meal.mark_completed()
        db.session.commit()
        flash("Meal completed!", "success")
    return redirect(url_for('dashboard.nutrition'))


# ==============================
# SKIP MEAL (NEW)
# ==============================
@dashboard.route('/skip_meal/<int:id>')
@user_required
def skip_meal(id):
    meal = DietPlan.query.get_or_404(id)
    if meal.user_id == current_user.id:
        meal.status = "Skipped"
        db.session.commit()
        flash("Meal marked as skipped.", "info")
    return redirect(url_for('dashboard.nutrition'))


# ==============================
# LOG MEAL (photo + type only)
# ==============================
@dashboard.route('/log-meal', methods=['POST'])
@user_required
def log_meal():
    meal_type = request.form.get('meal_type', 'General')
    calories = request.form.get('calories', 0)
    protein = request.form.get('protein', 0)

    try:
        calories = float(calories) if calories else 0.0
        protein = float(protein) if protein else 0.0
    except ValueError:
        calories = 0.0
        protein = 0.0

    # Require an image
    if 'meal_image' not in request.files or not request.files['meal_image'].filename:
        flash("Please select a meal photo to upload.", "error")
        return redirect(url_for('dashboard.nutrition'))

    file = request.files['meal_image']
    from flask import current_app
    import uuid
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in {'jpg', 'jpeg', 'png', 'webp', 'gif'}:
        flash("Invalid file type. Use JPG, PNG, or WEBP.", "error")
        return redirect(url_for('dashboard.nutrition'))

    image_filename = f"meal_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'meals')
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, image_filename))

    log = NutritionLog(
        user_id=current_user.id,
        meal_name=meal_type,   # use meal type as label
        meal_type=meal_type,
        meal_image=image_filename,
        calories=calories,
        protein=protein,
        carbohydrates=0.0,
        fat=0.0,
        date=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()
    flash(f"✅ {meal_type} photo logged!", "success")
    return redirect(url_for('dashboard.nutrition'))

@dashboard.route('/log-sleep', methods=['POST'])
@user_required
def log_sleep():
    try:
        hours = float(request.form.get('hours', 0))
        if hours > 0:
            from app.models.sleep import SleepLog
            log = SleepLog(
                user_id=current_user.id,
                hours=hours,
                date=datetime.utcnow().date()
            )
            db.session.add(log)
            db.session.commit()
            flash(f"🌙 {hours} hours of sleep logged!", "success")
        else:
            flash("Please enter a valid number of hours.", "error")
    except Exception as e:
        flash(f"Error logging sleep: {str(e)}", "error")
    
    return redirect(url_for('dashboard.index'))


# ==============================
# MEAL ANALYSIS
# ==============================
@dashboard.route('/analyze_meal', methods=['POST'])
@login_required
def analyze_meal():
    file = request.files["meal_image"]
    filename = secure_filename(file.filename)
    upload_path = os.path.join("app/static/uploads/meals", filename)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    file.save(upload_path)

    foods = detect_food(upload_path)
    food_name = foods[0] if foods else None
    nutrition = None

    if food_name:
        nutrition = get_food_nutrition(food_name)
        if nutrition:
            log = NutritionLog(
                user_id=current_user.id,
                meal_name=food_name,
                meal_image=filename,
                calories=nutrition["calories"]["value"],
                protein=nutrition["protein"]["value"],
                carbohydrates=nutrition["carbs"]["value"],
                fat=nutrition["fat"]["value"],
                date=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()

    return render_template(
        "dashboard/meal_result.html",
        food=food_name,
        nutrition=nutrition,
        image=filename
    )


# ==============================
# MEAL RECOMMENDATIONS
# ==============================
@dashboard.route('/meal-recommendations')
@user_required
def meal_recommendations():
    user = current_user
    workout = Workout.query.filter_by(user_id=user.id).order_by(Workout.date.desc()).first()
    workout_type = workout.workout_type if workout else None
    goal = Goal.query.filter_by(user_id=user.id).order_by(Goal.start_date.desc()).first()
    goal_type = goal.goal_type if goal else None
    meals = recommend_meals(goal=goal_type, workout_type=workout_type)
    return render_template(
        "dashboard/meal_recommendations.html",
        meals=meals,
        workout_type=workout_type,
        goal_type=goal_type
    )


# ==============================
# GOALS
# ==============================
@dashboard.route('/goals', methods=['GET', 'POST'])
@user_required
def goals():
    user = current_user
    if request.method == "POST":
        goal_type = request.form.get("goal_type")
        title = request.form.get("title")
        description = request.form.get("description")
        target_value = request.form.get("target_value", type=float)
        unit = request.form.get("unit")
        start_date = request.form.get("start_date")
        target_date = request.form.get("target_date")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if target_date:
            target_date = datetime.strptime(target_date, "%Y-%m-%d")

        new_goal = Goal(
            user_id=user.id,
            goal_type=goal_type,
            title=title,
            description=description,
            target_value=target_value,
            current_value=0,
            unit=unit,
            start_date=start_date,
            target_date=target_date
        )
        db.session.add(new_goal)
        db.session.commit()
        flash("Goal added successfully!", "success")
        return redirect(url_for("dashboard.goals"))

    active_goals = Goal.query.filter_by(user_id=user.id, completed=False).order_by(Goal.created_at.desc()).all()
    completed_goals = Goal.query.filter_by(user_id=user.id, completed=True).order_by(Goal.completed_at.desc()).all()
    
    return render_template("dashboard/goals.html", 
                         active_goals=active_goals, 
                         completed_goals=completed_goals)


@dashboard.route('/complete-goal/<int:goal_id>', methods=['POST'])
@login_required
def complete_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        flash("Unauthorized access!", "error")
        return redirect(url_for('dashboard.goals'))
    
    goal.completed = True
    goal.completed_at = datetime.utcnow()
    db.session.commit()
    flash(f"🎉 Congratulations! You've completed your goal: {goal.title}", "success")
    return redirect(url_for('dashboard.goals'))


@dashboard.route('/delete-goal/<int:goal_id>', methods=['POST'])
@login_required
def delete_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        flash("Unauthorized access!", "error")
        return redirect(url_for('dashboard.goals'))
    
    db.session.delete(goal)
    db.session.commit()
    flash("Goal deleted successfully.", "info")
    return redirect(url_for('dashboard.goals'))


# ==============================
# UNIFIED WORKOUT & MEAL HISTORY (REFINDED)
# ==============================
@dashboard.route('/history')
@user_required
def history():
    # Filter range (default 7 days)
    days_range = request.args.get('range', 7, type=int)
    category_filter = request.args.get('category', 'all') # 'all', 'workout', 'meal'
    
    start_date = datetime.utcnow() - timedelta(days=days_range)
    
    history_items = []

    # 1. Fetch Workout data
    if category_filter in ['all', 'workout']:
        w_plans = WorkoutPlan.query.filter(
            WorkoutPlan.user_id == current_user.id,
            WorkoutPlan.created_at >= start_date
        ).all()
        for item in w_plans:
            history_items.append({
                'date': item.created_at,
                'type': 'workout',
                'category': 'Workout Plan',
                'title': item.workout_name,
                'status': item.status,
                'icon': 'fa-dumbbell',
                'color': 'primary',
                'details': item.description or 'Assigned session'
            })
            
        w_logs = Workout.query.filter(
            Workout.user_id == current_user.id,
            Workout.date >= start_date
        ).all()
        for item in w_logs:
            history_items.append({
                'date': item.date,
                'type': 'workout',
                'category': 'Manual Workout',
                'title': item.workout_type,
                'status': 'Completed',
                'icon': 'fa-running',
                'color': 'success',
                'details': f"{item.duration}m - {item.calories_burned} kcal"
            })

    # 2. Fetch Meal data
    if category_filter in ['all', 'meal']:
        d_plans = DietPlan.query.filter(
            DietPlan.user_id == current_user.id,
            DietPlan.created_at >= start_date
        ).all()
        for item in d_plans:
            history_items.append({
                'date': item.created_at,
                'type': 'meal',
                'category': 'Meal Plan',
                'title': item.meal_name,
                'status': item.status,
                'icon': 'fa-utensils',
                'color': 'warning',
                'details': f"{item.meal_type} - {item.calories} kcal"
            })
            
        n_logs = NutritionLog.query.filter(
            NutritionLog.user_id == current_user.id,
            (NutritionLog.date >= start_date) | (NutritionLog.created_at >= start_date)
        ).all()
        for item in n_logs:
            history_items.append({
                'date': item.date or item.created_at,
                'type': 'meal',
                'category': 'Manual Meal',
                'title': item.meal_name,
                'status': 'Logged',
                'icon': 'fa-apple-alt',
                'color': 'info',
                'details': f"{item.calories} kcal - {item.meal_type}"
            })
    
    # Sort history descending
    history_items.sort(key=lambda x: x['date'], reverse=True)
    
    # Group by date for the template
    grouped_history = {}
    for item in history_items:
        day_key = item['date'].strftime('%Y-%m-%d')
        if day_key not in grouped_history:
            grouped_history[day_key] = {
                'date_obj': item['date'],
                'date_str': item['date'].strftime('%A, %b %d'),
                'workouts': [],
                'meals': []
            }
        
        if item['type'] == 'workout':
            grouped_history[day_key]['workouts'].append(item)
        else:
            grouped_history[day_key]['meals'].append(item)
            
    # Convert to sorted list of days
    sorted_days = sorted(grouped_history.keys(), reverse=True)
    history_data = [grouped_history[day] for day in sorted_days]
    
    return render_template(
        'dashboard/history.html', 
        history_data=history_data, 
        days_range=days_range,
        category_filter=category_filter,
        total_count=len(history_items)
    )


# ==============================
# PROFILE
# ==============================
@dashboard.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user

    if request.method == "POST":
        # Update text fields
        user.name = request.form.get("name")
        user.email = request.form.get("email")
        user.age = request.form.get("age")
        user.height = request.form.get("height")
        user.weight = request.form.get("weight")
        user.gender = request.form.get("gender")
        user.activity_level = request.form.get("activity_level")

        # ✅ FIXED: Handle Profile Picture Upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']

            # Check if file is selected and is valid
            if file and file.filename != '':
                # Check file extension
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                filename = file.filename
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

                if ext in allowed_extensions:
                    # Create unique filename
                    import os
                    from werkzeug.utils import secure_filename
                    import uuid

                    # Generate unique filename
                    unique_filename = f"{user.id}_{uuid.uuid4().hex[:8]}.{ext}"

                    # Create upload directory if it doesn't exist
                    from flask import current_app
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
                    os.makedirs(upload_folder, exist_ok=True)

                    # Save file
                    file_path = os.path.join(upload_folder, unique_filename)
                    file.save(file_path)

                    # ✅ Delete old profile picture if exists
                    if user.profile_pic and user.profile_pic != "default.png":
                        old_file_path = os.path.join(upload_folder, user.profile_pic)
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)

                    # Update database
                    user.profile_pic = unique_filename

                    flash("Profile picture updated successfully!", "success")
                else:
                    flash("Invalid file type. Please upload PNG, JPG, or GIF.", "error")

        # ✅ Commit all changes to database
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("dashboard.profile"))

    # GET request - show profile page
    bmi = user.calculate_bmi()
    bmr = user.calculate_bmr()
    tdee = user.calculate_tdee()

    return render_template(
        "dashboard/profile.html",
        user=user,
        bmi=bmi,
        bmr=bmr,
        tdee=tdee
    )

@dashboard.route('/complete-workout-plan/<int:plan_id>', methods=['POST'])
@login_required
def complete_workout_plan(plan_id):
    plan = WorkoutPlan.query.get_or_404(plan_id)
    
    if plan.user_id != current_user.id:
        flash("Unauthorized access!", "error")
        return redirect(url_for('dashboard.index'))
    
    # Mark plan as completed
    plan.mark_completed()
    
    # Create a real Workout log entry to reflect in analytics
    new_workout = Workout(
        user_id=current_user.id,
        workout_type=plan.workout_name,
        duration=plan.duration,
        calories_burned=plan.calories_to_burn,
        date=datetime.utcnow(),
        exercises=plan.description
    )
    db.session.add(new_workout)
    
    # Log Activity
    activity = Activity(
        user_id=current_user.id,
        action=f"Completed assigned workout: {plan.workout_name}",
        date=datetime.utcnow()
    )
    db.session.add(activity)
    
    db.session.commit()
    flash(f"🎉 Great job! Workout '{plan.workout_name}' completed. {plan.calories_to_burn} kcal burned!", "success")
    
    return redirect(url_for('dashboard.index'))

@dashboard.route('/complete-diet-plan/<int:plan_id>', methods=['POST'])
@login_required
def complete_diet_plan(plan_id):
    plan = DietPlan.query.get_or_404(plan_id)
    
    if plan.user_id != current_user.id:
        flash("Unauthorized access!", "error")
        return redirect(url_for('dashboard.index'))
    
    # Mark plan as completed
    plan.mark_completed()
    
    # Create a real NutritionLog entry
    new_log = NutritionLog(
        user_id=current_user.id,
        meal_name=plan.meal_name,
        meal_type=plan.meal_type,
        calories=plan.calories,
        protein=0,
        carbohydrates=0,
        fat=0,
        date=datetime.utcnow()
    )
    db.session.add(new_log)
    
    db.session.commit()
    flash(f"✅ Meal '{plan.meal_name}' marked as completed!", "success")
    
    return redirect(url_for('dashboard.index'))

# ==============================
# SUPPORT TICKETS
# ==============================
@dashboard.route('/support', methods=['GET', 'POST'])
@user_required
def support():
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not subject or not message:
            flash("Subject and Message are required.", "error")
        else:
            ticket = SupportTicket(
                user_id=current_user.id,
                subject=subject,
                message=message,
                status="Pending"
            )
            db.session.add(ticket)
            db.session.commit()
            flash("Your support request has been submitted successfully.", "success")
            return redirect(url_for('dashboard.support'))

    # GET request
    tickets = SupportTicket.query.filter_by(user_id=current_user.id).order_by(SupportTicket.created_at.desc()).all()
    return render_template("dashboard/support.html", tickets=tickets)

# ==============================
# SETTINGS
# ==============================
@dashboard.route('/settings', methods=['GET', 'POST'])
@user_required
def settings():
    if request.method == 'POST':
        user = current_user
        user.name = request.form.get('name', user.name)
        user.mobile_number = request.form.get('mobile_number', user.mobile_number)
        user.age = request.form.get('age', user.age)
        user.gender = request.form.get('gender', user.gender)
        user.height = request.form.get('height', user.height)
        user.weight = request.form.get('weight', user.weight)
        user.preferred_units = request.form.get('preferred_units', user.preferred_units)
        user.profile_private = 'profile_private' in request.form
        user.notifications_enabled = 'notifications_enabled' in request.form
        if request.form.get('activity_level'):
            user.activity_level = request.form.get('activity_level')
        db.session.commit()
        flash("Settings updated successfully!", "success")
        return redirect(url_for('dashboard.settings'))
    return render_template('dashboard/settings.html')

# ==============================
# NOTIFICATIONS
# ==============================
@dashboard.route('/notifications')
@user_required
def notifications():
    # Fetch all notifications for the user + global notifications
    from sqlalchemy import or_
    notifs = Notification.query.filter(
        or_(
            Notification.user_id == current_user.id,
            Notification.user_id == None
        )
    ).order_by(Notification.created_at.desc()).all()
    
    return render_template('dashboard/notifications.html', notifications=notifs)

@dashboard.route('/notification/read/<int:id>')
@user_required
def mark_read(id):
    notif = Notification.query.get_or_404(id)
    # Security check: can only mark their own or global as read
    if notif.user_id is None or notif.user_id == current_user.id:
        notif.is_read = True
        db.session.commit()
    return redirect(url_for('dashboard.notifications'))