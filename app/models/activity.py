from app.extensions import db
from datetime import datetime

class Activity(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('activities', lazy=True))

    def __init__(self, **kwargs):
        super(Activity, self).__init__(**kwargs)