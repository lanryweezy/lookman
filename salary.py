from flask import Blueprint
from user import db
from datetime import datetime

salary_bp = Blueprint('salary', __name__)

class SalaryCalculation(db.Model):
    __tablename__ = 'salary_calculations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    calculation_period = db.Column(db.String(20), nullable=False)  # Format: YYYY-MM
    base_salary = db.Column(db.Numeric(10, 2), default=0.00)
    commission_rate = db.Column(db.Numeric(5, 2), default=0.00)
    total_collections = db.Column(db.Numeric(10, 2), default=0.00)
    commission_amount = db.Column(db.Numeric(10, 2), default=0.00)
    total_salary = db.Column(db.Numeric(10, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def calculate_commission(self):
        """Calculate commission based on total collections and commission rate"""
        if self.total_collections and self.commission_rate:
            self.commission_amount = (self.total_collections * self.commission_rate) / 100
        return self.commission_amount

    def calculate_total_salary(self):
        """Calculate total salary (base + commission)"""
        self.total_salary = (self.base_salary or 0) + (self.commission_amount or 0)
        return self.total_salary

    def __repr__(self):
        return f'<SalaryCalculation {self.user.full_name if self.user else "Unknown"} - {self.calculation_period}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'calculation_period': self.calculation_period,
            'base_salary': float(self.base_salary),
            'commission_rate': float(self.commission_rate),
            'total_collections': float(self.total_collections),
            'commission_amount': float(self.commission_amount),
            'total_salary': float(self.total_salary),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

