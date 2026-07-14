from app.extensions import db
from app.models import User


# =========================
# REGISTER USER
# =========================
def register_user(name, email, password, age, height, weight, role, mobile_number=None):

    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return {"success": False, "message": "Email already registered"}
        
    if mobile_number:
        existing_mobile = User.query.filter_by(mobile_number=mobile_number).first()
        if existing_mobile:
            return {"success": False, "message": "Mobile number already registered"}

    # Create new user with role
    user = User(
        name=name,
        email=email,
        mobile_number=mobile_number,
        age=age,
        height=height,
        weight=weight,
        role=role  # 🔥 Important
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return {"success": True, "message": "User registered successfully"}


# =========================
# AUTHENTICATE USER
# =========================
def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        return user

    return None


# =========================
# OTP AUTHENTICATION
# =========================
import random
import string
from datetime import datetime, timedelta
import os

def generate_and_send_otp(mobile_number):
    existing_mobile = User.query.filter_by(mobile_number=mobile_number).first()
    if existing_mobile:
        return {"success": False, "message": "Mobile number already registered"}

    # Generate 6-digit OTP
    otp_code = ''.join(random.choices(string.digits, k=6))

    # Send SMS
    try:
        from twilio.rest import Client
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_phone = os.getenv("TWILIO_PHONE_NUMBER")
        
        if account_sid and auth_token and from_phone:
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=f"Your SmartFit verification code is: {otp_code}",
                from_=from_phone,
                to=mobile_number
            )
            print(f"Twilio message sent: {message.sid}")
        else:
            print(f"WARNING: Twilio credentials not fully set. DUMMY SENDED OTP for {mobile_number}: {otp_code}")
    except ImportError:
        print(f"WARNING: twilio module not installed. DUMMY SENDED OTP for {mobile_number}: {otp_code}")
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return {"success": False, "message": "Failed to send SMS."}

    return {"success": True, "message": "OTP sent successfully", "otp_code": otp_code}

def verify_otp_for_login(mobile_number, otp_code):
    user = User.query.filter_by(mobile_number=mobile_number).first()
    if not user:
        return None

    if user.otp_code != otp_code:
        return None

    # Check expiry
    if user.otp_expiry and datetime.utcnow() > user.otp_expiry:
        return None

    # Clear OTP after successful use
    user.otp_code = None
    user.otp_expiry = None
    db.session.commit()
    
    return user