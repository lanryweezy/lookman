from flask import Blueprint
from user import db
from datetime import datetime

salary_bp = Blueprint('salary', __name__)

# Model Definition
class SalaryCalculation(db.Model):
    __tablename__ = 'salary_calculations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    calculation_period = db.Column(db.String(20), nullable=False)
    base_salary = db.Column(db.Numeric(10, 2), default=0.00)
    commission_rate = db.Column(db.Numeric(5, 2), default=0.00)
    total_collections = db.Column(db.Numeric(10, 2), default=0.00)
    commission_amount = db.Column(db.Numeric(10, 2), default=0.00)
    total_salary = db.Column(db.Numeric(10, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
