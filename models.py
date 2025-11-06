from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
import uuid  # For member IDs

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_date = db.Column(db.Date, default=date.today, nullable=False)
    service_type = db.Column(db.String(20), nullable=False)

    adults_men       = db.Column(db.Integer, default=0, nullable=False)
    adults_women     = db.Column(db.Integer, default=0, nullable=False)
    youth_gents      = db.Column(db.Integer, default=0, nullable=False)
    youth_ladies     = db.Column(db.Integer, default=0, nullable=False)
    children_boys    = db.Column(db.Integer, default=0, nullable=False)
    children_girls   = db.Column(db.Integer, default=0, nullable=False)
    visitors_male    = db.Column(db.Integer, default=0, nullable=False)
    visitors_female  = db.Column(db.Integer, default=0, nullable=False)


class Offering(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_date = db.Column(db.Date, default=date.today, nullable=False)
    service_type = db.Column(db.String(20), nullable=False)

    first_offering  = db.Column(db.Float, default=0.0, nullable=False)
    second_offering = db.Column(db.Float, default=0.0, nullable=False)


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4())[:8])  # e.g., 'a1b2c3d4'
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # 'Male', 'Female'
    age_group = db.Column(db.String(20), nullable=False)  # 'Adult', 'Youth', 'Child'
    contact = db.Column(db.String(50))  # Phone/email
    join_date = db.Column(db.Date, default=date.today)


class Fund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # e.g., 'Building Fund'
    description = db.Column(db.Text)
    created_date = db.Column(db.Date, default=date.today)


class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    service_date = db.Column(db.Date, default=date.today, nullable=False)
    service_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))  # Optional
    fund = db.relationship('Fund', backref='contributions')
    member = db.relationship('Member', backref='contributions')


class MonthlyBudget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month_year = db.Column(db.String(7), nullable=False)  # e.g., '2025-11'
    service_type = db.Column(db.String(20), nullable=False)

    target_attendance = db.Column(db.Integer, default=0, nullable=False)
    target_offering = db.Column(db.Float, default=0.0, nullable=False)