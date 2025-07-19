from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    role = db.Column(db.Enum('admin', 'account_officer', name='user_roles'), 
                     default='account_officer', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_first_login = db.Column(db.Boolean, default=True, nullable=False)
    last_password_change = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    created_borrowers = db.relationship('Borrower', backref='creator', lazy=True, foreign_keys='Borrower.created_by')
    managed_loans = db.relationship('Loan', backref='account_officer', lazy=True, foreign_keys='Loan.account_officer_id')
    recorded_payments = db.relationship('Payment', backref='recorder', lazy=True, foreign_keys='Payment.recorded_by')
    salary_calculations = db.relationship('SalaryCalculation', backref='user', lazy=True)
    settings_updates = db.relationship('SystemSetting', backref='updater', lazy=True, foreign_keys='SystemSetting.updated_by')

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
        self.last_password_change = datetime.utcnow()
        self.is_first_login = False

    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'

    def is_account_officer(self):
        """Check if user is account officer"""
        return self.role == 'account_officer'

    def __repr__(self):
        return f'<User {self.username}>'


from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field

class UserSchema(SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True

    id = auto_field(dump_only=True)
    username = auto_field()
    full_name = auto_field()
    email = auto_field()
    phone = auto_field()
    role = auto_field()
    is_active = auto_field()
    is_first_login = auto_field()
    last_password_change = auto_field()
    created_at = auto_field()
    updated_at = auto_field()

# Blueprint for user-related endpoints
user_bp = Blueprint('user', __name__)
