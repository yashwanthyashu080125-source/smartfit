from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.services.auth_service import register_user, authenticate_user, generate_and_send_otp
from flask import jsonify, session

bp = Blueprint("auth", __name__, url_prefix="/auth")


# =========================
# REGISTER
# =========================
@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")

        password = request.form.get("password")
        age = request.form.get("age")
        height = request.form.get("height")
        weight = request.form.get("weight")

        # 🔥 SECURITY FIX (IMPORTANT)
        role = "user"

        result = register_user(name, email, password, age, height, weight, role)

        if result["success"]:
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash(result["message"], "danger")

    return render_template("auth/register.html")


# =========================
# LOGIN
# =========================
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = authenticate_user(email, password)

        if user:
            login_user(user)

            # Redirect based on role
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            else:
                return redirect(url_for("dashboard.index"))

        flash("Invalid credentials", "danger")

    return render_template("auth/login.html")

# =========================
# OTP REGISTER ROUTES
# =========================
@bp.route("/request_otp", methods=["POST"])
def request_otp():
    data = request.json or request.form
    mobile_number = data.get("mobile_number")
    result = generate_and_send_otp(mobile_number)
    
    if result.get("success") and "otp_code" in result:
        session['registration_otp'] = result['otp_code']
        # Avoid sending code back directly below
        return jsonify({"success": True, "message": "OTP sent successfully"})
        
    return jsonify(result)


# =========================
# LOGOUT
# =========================
@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))