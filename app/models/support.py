from datetime import datetime
from app.extensions import db

class SupportTicket(db.Model):
    __tablename__ = "support_tickets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    admin_reply = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="Pending")
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to user
    user = db.relationship('User', backref=db.backref('support_tickets', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<SupportTicket {self.id} - {self.subject}>"
