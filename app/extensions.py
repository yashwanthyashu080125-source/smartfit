from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Database
db = SQLAlchemy()

# Login Manager
login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    # Import inside function to avoid circular import
    from app.models import User
    return User.query.get(int(user_id))