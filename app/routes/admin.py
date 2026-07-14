from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
import csv
import io
from flask_login import current_user
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import or_
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
from app.models.contact import ContactMessage

# ✅ FIXED: Use __name__ instead of name
bp = Blueprint("admin", __name__, url_prefix="/admin")


# ==========================
# ADMIN DECORATOR
# ==========================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role != "admin":
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)

    return decorated_function


# ==========================
# DASHBOARD
# ==========================
@bp.route("/")
@admin_required
def dashboard():
    total_users = User.query.count()
    total_workouts = Workout.query.count()
    total_meals = NutritionLog.query.count()
    total_goals = Goal.query.count()

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_users = User.query.filter(User.last_login >= week_ago).count()
    workouts_this_week = Workout.query.filter(Workout.date >= week_ago).count()

    users_with_metrics = User.query.filter(
        User.height.isnot(None),
        User.weight.isnot(None)
    ).all()

    avg_bmi = None
    if users_with_metrics:
        bmi_values = []
        for u in users_with_metrics:
            if u.height and u.height > 0 and u.weight and u.weight > 0:
                bmi = round(u.weight / ((u.height / 100) ** 2), 1)
                bmi_values.append(bmi)
        if bmi_values:
            avg_bmi = round(sum(bmi_values) / len(bmi_values), 1)

    # Recent Activities
    recent_activities = Activity.query.order_by(Activity.date.desc()).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_workouts=total_workouts,
        total_meals=total_meals,
        total_goals=total_goals,
        recent_users=recent_users,
        active_users=active_users,
        workouts_this_week=workouts_this_week,
        avg_bmi=avg_bmi,
        recent_activities=recent_activities
    )


# ==========================
# USER MANAGEMENT
# ==========================
@bp.route("/users")
@admin_required
def users():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    query = User.query.filter(User.role != "admin")

    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    users_paginated = query.order_by(User.created_at.desc()).paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    return render_template(
        "admin/users.html",
        users=users_paginated,
        search=search,
    )


# ==========================
# USER DETAIL - ENHANCED
# ==========================
@bp.route("/users/<int:user_id>")
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)

    # User workouts
    user_workouts = Workout.query.filter_by(user_id=user_id).order_by(
        Workout.date.desc()
    ).limit(10).all()

    # User nutrition
    user_nutrition = NutritionLog.query.filter_by(user_id=user_id).order_by(
        NutritionLog.date.desc()
    ).limit(10).all()

    # User goals
    user_goals = Goal.query.filter_by(user_id=user_id).all()

    # ✅ NEW: Admin assigned workout plans
    workout_plans = WorkoutPlan.query.filter_by(user_id=user_id).order_by(
        WorkoutPlan.created_at.desc()
    ).all()

    # ✅ NEW: Admin assigned diet plans
    diet_plans = DietPlan.query.filter_by(user_id=user_id).order_by(
        DietPlan.created_at.desc()
    ).all()

    # ✅ NEW: User activities
    user_activities = Activity.query.filter_by(user_id=user_id).order_by(
        Activity.date.desc()
    ).limit(15).all()

    # ✅ NEW: Sleep logs
    from app.models.sleep import SleepLog
    user_sleep = SleepLog.query.filter_by(user_id=user_id).order_by(
        SleepLog.date.desc()
    ).limit(15).all()

    # Statistics
    total_workouts = Workout.query.filter_by(user_id=user_id).count()
    total_calories = db.session.query(
        db.func.sum(Workout.calories_burned)
    ).filter_by(user_id=user_id).scalar() or 0
    total_meals = NutritionLog.query.filter_by(user_id=user_id).count()
    total_plans = len(workout_plans) + len(diet_plans)

    # Calculate BMI
    bmi = user.calculate_bmi()
    bmi_category = user.bmi_category()

    return render_template(
        "admin/user_detail.html",
        user=user,
        user_workouts=user_workouts,
        user_nutrition=user_nutrition,
        user_goals=user_goals,
        workout_plans=workout_plans,
        diet_plans=diet_plans,
        user_activities=user_activities,
        user_sleep=user_sleep,
        total_workouts=total_workouts,
        total_calories=total_calories,
        total_meals=total_meals,
        total_plans=total_plans,
        bmi=bmi,
        bmi_category=bmi_category,
    )


# ==========================
# DELETE USER
# ==========================
@bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("Cannot delete your own account.", "error")
        return redirect(url_for("admin.users"))

    try:
        Workout.query.filter_by(user_id=user_id).delete()
        NutritionLog.query.filter_by(user_id=user_id).delete()
        Goal.query.filter_by(user_id=user_id).delete()
        WorkoutPlan.query.filter_by(user_id=user_id).delete()
        DietPlan.query.filter_by(user_id=user_id).delete()
        Activity.query.filter_by(user_id=user_id).delete()
        SupportTicket.query.filter_by(user_id=user_id).delete()

        db.session.delete(user)
        db.session.commit()

        flash("User deleted successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {str(e)}", "error")

    return redirect(url_for("admin.users"))


# ==========================
# PLANS (WORKOUT + DIET)
# ==========================
@bp.route("/plans", methods=["GET", "POST"])
@admin_required
def plans():
    users = User.query.filter(User.role != "admin").all()
    selected_user = None
    user_history = {'workouts': [], 'diets': []}


    user_id = request.args.get("user_id") or request.form.get("user_id")

    if user_id:
        selected_user = User.query.get(int(user_id))
        if selected_user:
            user_history['workouts'] = WorkoutPlan.query.filter_by(
                user_id=selected_user.id
            ).order_by(WorkoutPlan.created_at.desc()).all()

            user_history['diets'] = DietPlan.query.filter_by(
                user_id=selected_user.id
            ).order_by(DietPlan.created_at.desc()).all()

    if request.method == "POST":
        if not selected_user:
            flash("Please select a user first.", "error")
            return redirect(url_for("admin.plans"))

        selected_days = request.form.getlist("days")
        if not selected_days:
            selected_days = ["All Days"]

        # 1. Workout Detection & Saving
        workout_name = request.form.get("workout_name")
        if workout_name:
            workout_image_filename = None
            if "workout_image" in request.files:
                file = request.files["workout_image"]
                if file and file.filename != '':
                    import os
                    import uuid
                    from flask import current_app
                    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                    if ext in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
                        unique_filename = f"workout_{uuid.uuid4().hex[:8]}.{ext}"
                        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'workouts')
                        os.makedirs(upload_folder, exist_ok=True)
                        file.save(os.path.join(upload_folder, unique_filename))
                        workout_image_filename = unique_filename

            for day in selected_days:
                plan = WorkoutPlan(
                    user_id=selected_user.id,
                    workout_name=workout_name,
                    description=request.form.get("description"),
                    duration=request.form.get("duration", type=int),
                    difficulty=request.form.get("difficulty"),
                    calories_to_burn=request.form.get("calories_to_burn", type=int) or 0,
                    day_of_week=day,
                    status="Pending",
                    image_filename=workout_image_filename,
                    created_at=datetime.utcnow()
                )
                db.session.add(plan)

        # 2. Diet Detection & Saving
        meal_types = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
        for mt in meal_types:
            prefix = mt.lower()
            name = request.form.get(f"{prefix}_name")
            if name:
                for day in selected_days:
                    plan = DietPlan(
                        user_id=selected_user.id,
                        meal_type=mt,
                        meal_name=name,
                        calories=request.form.get(f"{prefix}_calories", type=int) or 0,
                        description=request.form.get(f"{prefix}_description"),
                        intake_time=request.form.get(f"{prefix}_time"),
                        day_of_week=day,
                        status="Pending",
                        created_at=datetime.utcnow()
                    )
                    db.session.add(plan)

        db.session.commit()
        flash(f"Plans assigned successfully for {', '.join(selected_days)}!", "success")
        return redirect(url_for("admin.plans", user_id=selected_user.id))

    return render_template(
        "admin/plans.html",
        users=users,
        selected_user=selected_user,
        user_history=user_history
    )

# ==========================
# EDIT WORKOUT PLAN
# ==========================
@bp.route("/plans/<int:plan_id>/edit-workout", methods=["POST"])
@admin_required
def edit_workout_plan(plan_id):
    plan = WorkoutPlan.query.get_or_404(plan_id)
    plan.workout_name = request.form.get("workout_name")
    plan.description = request.form.get("description")
    plan.duration = request.form.get("duration", type=int)
    plan.difficulty = request.form.get("difficulty")
    plan.day_of_week = request.form.get("day_of_week")
    plan.calories_to_burn = request.form.get("calories_to_burn", type=int) or 0
    
    # Handle Image Update
    if "workout_image" in request.files:
        file = request.files["workout_image"]
        if file and file.filename != '':
            import os
            import uuid
            from flask import current_app
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if ext in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
                # Delete old image if exists
                if plan.image_filename:
                    old_path = os.path.join(current_app.root_path, 'static', 'uploads', 'workouts', plan.image_filename)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except:
                            pass
                
                unique_filename = f"workout_{uuid.uuid4().hex[:8]}.{ext}"
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'workouts')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, unique_filename))
                plan.image_filename = unique_filename
    
    db.session.commit()
    flash("Workout plan updated successfully!", "success")
    return redirect(url_for("admin.plans", user_id=plan.user_id))

# ==========================
# EDIT DIET PLAN
# ==========================
@bp.route("/plans/<int:plan_id>/edit-diet", methods=["POST"])
@admin_required
def edit_diet_plan(plan_id):
    plan = DietPlan.query.get_or_404(plan_id)
    plan.meal_name = request.form.get("meal_name")
    plan.meal_type = request.form.get("meal_type")
    plan.calories = request.form.get("calories", type=int) or 0
    plan.description = request.form.get("description")
    plan.intake_time = request.form.get("intake_time")
    plan.day_of_week = request.form.get("day_of_week")
    
    db.session.commit()
    flash("Diet plan updated successfully!", "success")
    return redirect(url_for("admin.plans", user_id=plan.user_id))


# ==========================
# UPDATE PLAN STATUS
# ==========================
@bp.route("/plans/<int:plan_id>/update-status", methods=["POST"])
@admin_required
def update_plan_status(plan_id):
    plan = WorkoutPlan.query.get(plan_id)
    plan_type = "workout"

    if not plan:
        plan = DietPlan.query.get(plan_id)
        plan_type = "diet"

    if plan:
        new_status = request.form.get("status")
        plan.status = new_status
        db.session.commit()
        flash(f"{plan_type.capitalize()} plan status updated to {new_status}", "success")

    return redirect(request.referrer or url_for("admin.plans"))


# ==========================
# DELETE WORKOUT PLAN
# ==========================
@bp.route("/plans/<int:plan_id>/delete-workout", methods=["POST"])
@admin_required
def delete_workout_plan(plan_id):
    plan = WorkoutPlan.query.get_or_404(plan_id)
    user_id = plan.user_id

    try:
        db.session.delete(plan)
        db.session.commit()
        flash("Workout plan deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting plan: {str(e)}", "error")

    return redirect(url_for("admin.plans", user_id=user_id))


# ==========================
# DELETE DIET PLAN
# ==========================
@bp.route("/plans/<int:plan_id>/delete-diet", methods=["POST"])
@admin_required
def delete_diet_plan(plan_id):
    plan = DietPlan.query.get_or_404(plan_id)
    user_id = plan.user_id

    try:
        db.session.delete(plan)
        db.session.commit()
        flash("Diet plan deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting plan: {str(e)}", "error")

    return redirect(url_for("admin.plans", user_id=user_id))


# ==========================
# DELETE PLAN FROM USER DETAIL
# ==========================
@bp.route("/users/<int:user_id>/plans/<int:plan_id>/delete", methods=["POST"])
@admin_required
def delete_plan_from_user_detail(user_id, plan_id):
    plan_type = request.form.get("plan_type")

    try:
        if plan_type == "workout":
            plan = WorkoutPlan.query.get_or_404(plan_id)
        else:
            plan = DietPlan.query.get_or_404(plan_id)

        if plan.user_id != user_id:
            flash("Unauthorized access!", "error")
            return redirect(url_for("admin.user_detail", user_id=user_id))

        db.session.delete(plan)
        db.session.commit()
        flash(f"{plan_type.capitalize()} plan deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting plan: {str(e)}", "error")

    return redirect(url_for("admin.user_detail", user_id=user_id))


# ==========================
# USER PROGRESS
# ==========================
@bp.route("/user-progress")
@admin_required
def user_progress():
    users = User.query.filter(User.role != 'admin').all()
    progress_data = []

    for user in users:
        total_workouts = Workout.query.filter_by(user_id=user.id).count()
        total_calories = db.session.query(
            db.func.sum(Workout.calories_burned)
        ).filter_by(user_id=user.id).scalar() or 0
        total_meals = NutritionLog.query.filter_by(user_id=user.id).count()
        
        # Calculate overall goal progress
        goals = Goal.query.filter_by(user_id=user.id).all()
        avg_goal_progress = 0
        if goals:
            avg_goal_progress = sum([g.calculate_progress() for g in goals]) / len(goals)

        # Calculate a "Performance Score" (0-100)
        # Weight: Workouts (50%), Calories (20%), Meals (30%)
        # Normalizing against targets or averages
        perf_score = min(100, (total_workouts * 5) + (total_calories / 100) + (total_meals * 2))

        progress_data.append({
            "user": user,
            "workouts": total_workouts,
            "calories": total_calories,
            "meals": total_meals,
            "goal_progress": round(avg_goal_progress, 1),
            "performance_score": round(perf_score, 1),
            "last_active": user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
        })

    # Sort by performance score desc
    progress_data.sort(key=lambda x: x['performance_score'], reverse=True)

    return render_template(
        "admin/user_progress.html",
        progress_data=progress_data
    )


# ==========================
# ANALYTICS
# ==========================
@bp.route("/analytics")
@admin_required
def analytics():
    # 1. Monthly Totals
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    monthly_users = User.query.filter(User.created_at >= thirty_days_ago).count()
    monthly_workouts = Workout.query.filter(Workout.date >= thirty_days_ago).count()
    monthly_meals = NutritionLog.query.filter(NutritionLog.date >= thirty_days_ago).count()

    # 2. Daily Data for Charts (Last 14 days)
    fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
    dates = [(datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(13, -1, -1)]
    
    workout_counts = []
    meal_counts = []
    user_counts = []
    
    for d_str in dates:
        d = datetime.strptime(d_str, '%Y-%m-%d').date()
        workout_counts.append(Workout.query.filter(db.func.date(Workout.date) == d).count())
        meal_counts.append(NutritionLog.query.filter(db.func.date(NutritionLog.date) == d).count())
        user_counts.append(User.query.filter(db.func.date(User.created_at) == d).count())

    # 3. Goal Distribution
    goal_types = db.session.query(Goal.goal_type, db.func.count(Goal.id)).group_by(Goal.goal_type).all()
    goal_labels = [gt[0].replace('_', ' ').capitalize() for gt in goal_types]
    goal_data = [gt[1] for gt in goal_types]

    # 4. Most Active Users
    most_active_users = db.session.query(
        User.id,
        User.name,
        db.func.count(Workout.id)
    ).join(Workout).group_by(User.id).order_by(
        db.func.count(Workout.id).desc()
    ).limit(5).all()

    return render_template(
        "admin/analytics.html",
        monthly_users=monthly_users,
        monthly_workouts=monthly_workouts,
        monthly_meals=monthly_meals,
        chart_labels=dates,
        workout_counts=workout_counts,
        meal_counts=meal_counts,
        user_counts=user_counts,
        goal_labels=goal_labels,
        goal_data=goal_data,
        most_active_users=most_active_users,
    )


# ==========================
# REPORTS
# ==========================
@bp.route("/reports")
@admin_required
def reports():
    # Overall Totals
    total_users = User.query.filter(User.role != 'admin').count()
    total_workouts = Workout.query.count()
    total_meals = NutritionLog.query.count()
    total_goals = Goal.query.count()

    # Weekly Stats
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_new_users = User.query.filter(User.created_at >= week_ago).count()
    weekly_workouts = Workout.query.filter(Workout.date >= week_ago).count()
    
    # Calculate Engagement Rate (Workouts per User)
    engagement_rate = 0
    if total_users > 0:
        engagement_rate = round(total_workouts / total_users, 1)

    # User List for Preview
    users_preview = User.query.filter(User.role != 'admin').order_by(User.created_at.desc()).limit(20).all()

    return render_template(
        "admin/reports.html",
        total_users=total_users,
        total_workouts=total_workouts,
        total_meals=total_meals,
        total_goals=total_goals,
        weekly_new_users=weekly_new_users,
        weekly_workouts=weekly_workouts,
        engagement_rate=engagement_rate,
        users_preview=users_preview,
        last_updated=datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    )


@bp.route("/export/users")
@admin_required
def export_users():
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['ID', 'Name', 'Email', 'Role', 'Age', 'Weight', 'Height', 'BMI', 'Created At', 'Last Login'])
    
    # Data
    users = User.query.all()
    for u in users:
        writer.writerow([
            u.id, u.name, u.email, u.role, u.age, u.weight, u.height, 
            u.calculate_bmi(), u.created_at, u.last_login
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=smartfit_users.csv"}
    )


# ==========================
# SETTINGS
# ==========================
@bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    if request.method == "POST":
        flash("Settings saved successfully!", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html")


# ==========================
# SUPPORT TICKETS
# ==========================
@bp.route("/support")
@admin_required
def support():
    # Order pending first, then by created_at descending
    tickets = SupportTicket.query.order_by(
        db.case(
            (SupportTicket.status == 'Pending', 1),
            else_=2
        ),
        SupportTicket.created_at.desc()
    ).all()
    return render_template("admin/support.html", tickets=tickets)


@bp.route("/support/<int:ticket_id>/reply", methods=["POST"])
@admin_required
def support_reply(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    reply_message = request.form.get("admin_reply")

    if reply_message:
        ticket.admin_reply = reply_message
        ticket.status = "Resolved"
        db.session.commit()
        flash("Reply submitted successfully.", "success")
    else:
        flash("Reply message cannot be empty.", "error")

    return redirect(url_for("admin.support"))

# ==========================
# GOAL TRACKER (BEST FIT)
# ==========================
@bp.route("/goals")
@admin_required
def goal_tracker():
    # Fetch all goals with their users
    all_goals = Goal.query.join(User).order_by(Goal.created_at.desc()).all()
    
    # Calculate some goal stats
    active_goals = Goal.query.filter_by(completed=False).count()
    completed_goals = Goal.query.filter_by(completed=True).count()
    
    goal_stats = {
        "active": active_goals,
        "completed": completed_goals,
        "total": len(all_goals),
        "success_rate": round((completed_goals / len(all_goals) * 100), 1) if all_goals else 0
    }
    
    return render_template(
        "admin/goals.html",
        goals=all_goals,
        stats=goal_stats
    )

# ==========================
# NOTIFICATIONS & REMINDERS
# ==========================
@bp.route("/notifications", methods=["GET", "POST"])
@admin_required
def notifications():
    if request.method == "POST":
        title = request.form.get("title")
        message = request.form.get("message")
        ntype = request.form.get("type", "info")
        user_id = request.form.get("user_id") # Null means global
        
        try:
            if user_id and user_id != "all":
                # Targeted Notification
                notif = Notification(
                    user_id=int(user_id),
                    title=title,
                    message=message,
                    type=ntype
                )
                db.session.add(notif)
            else:
                # Global Notification (Create one for each user or a special global flag)
                # For this implementation, we'll create for all users
                users = User.query.filter(User.role != 'admin').all()
                for user in users:
                    notif = Notification(
                        user_id=user.id,
                        title=title,
                        message=message,
                        type=ntype
                    )
                    db.session.add(notif)
            
            db.session.commit()
            flash("Notification sent successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error sending notification: {str(e)}", "error")
            
        return redirect(url_for("admin.notifications"))

    # GET request
    users = User.query.filter(User.role != 'admin').all()
    recent_notifications = Notification.query.order_by(Notification.created_at.desc()).limit(20).all()
    
    return render_template(
        "admin/notifications.html",
        users=users,
        notifications=recent_notifications
    )

@bp.route("/notifications/<int:notif_id>/delete", methods=["POST"])
@admin_required
def delete_notification(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    try:
        db.session.delete(notif)
        db.session.commit()
        flash("Notification removed.", "success")
    except:
        db.session.rollback()
        flash("Error deleting notification.", "error")
    return redirect(url_for("admin.notifications"))

# ==========================
# API ENDPOINTS
# ==========================
@bp.route("/api/stats")
@admin_required
def get_stats():
    return jsonify({
        "total_users": User.query.count(),
        "total_workouts": Workout.query.count(),
        "active_users_7d": User.query.filter(
            User.last_login >= datetime.utcnow() - timedelta(days=7)
        ).count()
    })
# ==========================
# CONTACT MESSAGES
# ==========================
@bp.route('/messages')
@admin_required
def messages():
    all_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/contact_messages.html', messages=all_messages)

@bp.route('/messages/<int:msg_id>/read', methods=['POST'])
@admin_required
def mark_message_read(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    msg.is_read = True
    db.session.commit()
    flash('Message marked as read.', 'success')
    return redirect(url_for('admin.messages'))

@bp.route('/messages/<int:msg_id>/delete', methods=['POST'])
@admin_required
def delete_message(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted successfully.', 'success')
    return redirect(url_for('admin.messages'))
