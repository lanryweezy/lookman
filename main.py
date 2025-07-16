import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_login import LoginManager
from flask_cors import CORS
from flask_migrate import Migrate
from user import db, User, user_bp
from borrowers import Borrower, borrowers_bp
from loans import Loan, loans_bp
from payments import Payment, payments_bp
from salary import SalaryCalculation, salary_bp
from settings import SystemSetting
from auth import auth_bp
from admin import admin_bp
from automation import automation_bp
from reports import reports_bp
from profile import profile_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'lookman-loan-management-secret-key-2024'

# Initialize CORS
CORS(app, supports_credentials=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(borrowers_bp, url_prefix='/api/borrowers')
app.register_blueprint(loans_bp, url_prefix='/api/loans')
app.register_blueprint(payments_bp, url_prefix='/api/payments')
app.register_blueprint(automation_bp, url_prefix='/api/automation')
app.register_blueprint(salary_bp, url_prefix='/api/salary')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(profile_bp, url_prefix='/api/profile')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

# Create tables and initialize default data
with app.app_context():
    db.create_all()
    
    # Create default admin user if it doesn't exist
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            full_name='System Administrator',
            role='admin'
        )
        admin_user.set_password('admin123')  # Default password - should be changed
        db.session.add(admin_user)
        db.session.commit()
        print("Default admin user created: username='admin', password='admin123'")
    
    # Initialize default system settings
    default_settings = [
        ('default_loan_duration', '15', 'Default loan duration in days'),
        ('default_interest_rate', '10.00', 'Default interest rate percentage'),
        ('weekend_payment_handling', 'next_business_day', 'How to handle weekend payments'),
        ('base_salary_default', '50000.00', 'Default base salary amount'),
        ('commission_rate_default', '5.00', 'Default commission rate percentage')
    ]
    
    for key, value, description in default_settings:
        existing_setting = SystemSetting.query.filter_by(setting_key=key).first()
        if not existing_setting:
            SystemSetting.set_setting(key, value, description, admin_user.id)

@app.route('/user_profile.html')
def serve_user_profile():
    """Serve user profile management page"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    
    profile_path = os.path.join(static_folder_path, 'user_profile.html')
    if os.path.exists(profile_path):
        return send_from_directory(static_folder_path, 'user_profile.html')
    else:
        return "user_profile.html not found", 404

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)