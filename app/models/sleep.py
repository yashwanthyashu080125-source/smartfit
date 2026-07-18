from app.extensions import db
from datetime import datetime

class SleepLog(db.Model):
    __tablename__ = 'sleep_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    quality = db.Column(db.String(20), nullable=True) # e.g. "Good", "Fair", "Poor"
    date = db.Column(db.Date, default=lambda: datetime.utcnow().date())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref=db.backref('sleep_logs', lazy=True))

    def __init__(self, **kwargs):
        super(SleepLog, self).__init__(**kwargs)

    def __repr__(self):
        return f'<SleepLog {self.user_id} - {self.hours}h on {self.date}>'
