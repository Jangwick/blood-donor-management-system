from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin  # Import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    registered_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_donation_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Donor {self.name}>"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    contact_number = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default='donor')  # donor, hospital, admin
    profile = db.relationship('DonorProfile', backref='user', uselist=False)
    donations = db.relationship('Donation', backref='donor', lazy=True)
    appointments = db.relationship('Appointment', backref='donor', lazy=True, 
                                 foreign_keys='Appointment.user_id')
    hospital_appointments = db.relationship('Appointment', backref='hospital', lazy=True,
                                         foreign_keys='Appointment.hospital_id')
    badges = db.relationship('Badge', secondary='user_badges', backref='users')

# ...existing code...
