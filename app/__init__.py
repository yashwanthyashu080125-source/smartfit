from flask import Flask, render_template, redirect, url_for
from flask_migrate import Migrate
from flask_login import current_user, login_required

from config import Config
from .extensions import db, login_manager

# ✅ Create migrate object globally
migrate = Migrate()


def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)

    # ==========================
    # Initialize Extensions
    # ==========================

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)   # ✅ FIXED

    # ==========================
    # Import Models (IMPORTANT)
    # ==========================

    from app.models.user import User
    from app.models.workout import Workout
    from app.models.nutrition import NutritionLog
    from app.models.goal import Goal

    # ✅ ADD THESE (VERY IMPORTANT)
    from app.models.workout_plan import WorkoutPlan
    from app.models.diet_plan import DietPlan
    from app.models.sleep import SleepLog
    from app.models.support import SupportTicket
    from app.models.contact import ContactMessage

    # Create tables automatically
    with app.app_context():
        db.create_all()

    # ==========================
    # Register Blueprints
    # ==========================

    from app.routes.auth import bp as auth_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.dashboard import dashboard as dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

    # ==========================
    # Public Routes
    # ==========================

    @app.route("/")
    def splash():
        return render_template("splash.html")

    @app.route("/home")
    def home():
        return render_template("home.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/features")
    def features():
        return render_template("features.html")

    @app.route("/fitness")
    def fitness():
        return render_template("fitness.html")

    @app.route("/nutrition")
    def nutrition():
        return render_template("nutrition.html")

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        from flask import request, flash, redirect
        from app.models.contact import ContactMessage
        from app.extensions import db
        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            subject = request.form.get("subject")
            message = request.form.get("message")

            if not all([name, email, subject, message]):
                flash("All fields are required.", "error")
                return redirect(url_for("contact"))

            new_msg = ContactMessage()
            new_msg.name = name
            new_msg.email = email
            new_msg.subject = subject
            new_msg.message = message
            db.session.add(new_msg)
            db.session.commit()

            flash("Success! Your message has been beamed to our support team. We'll respond shortly.", "success")
            return redirect(url_for("contact"))
        return render_template("contact.html")

    # ==========================
    # Redirect Dashboard
    # ==========================

    @app.route("/dashboard")
    @login_required
    def dashboard_redirect():

        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))

        return redirect(url_for("dashboard.index"))

    # ==========================
    # Error Pages
    # ==========================

    @app.context_processor
    def inject_notifications():
        if current_user.is_authenticated and current_user.role != 'admin':
            from app.models.notification import Notification
            from sqlalchemy import or_
            unread_count = Notification.query.filter(
                or_(Notification.user_id == current_user.id, Notification.user_id == None),
                Notification.is_read == False
            ).count()
            recent_notifs = Notification.query.filter(
                or_(Notification.user_id == current_user.id, Notification.user_id == None)
            ).order_by(Notification.created_at.desc()).limit(5).all()
            return dict(unread_notifs_count=unread_count, recent_notifs=recent_notifs)
        return dict(unread_notifs_count=0, recent_notifs=[])

    @app.errorhandler(404)
    def page_not_found(_):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(_):
        return render_template("errors/500.html"), 500

    return app