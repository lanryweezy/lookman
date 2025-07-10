# Lookman Loan Management System
## Technical Documentation

**Application URL**: https://60h5imce1zml.manus.space  
**Repository**: Local development files available  
**Technology Stack**: Python Flask, SQLAlchemy, Bootstrap, JavaScript

---

## Architecture Overview

### Technology Stack
- **Backend**: Python 3.11, Flask 2.x
- **Database**: SQLAlchemy ORM with SQLite
- **Frontend**: HTML5, CSS3, JavaScript (ES6), Bootstrap 5
- **Authentication**: Flask-Login with session management
- **Security**: CORS enabled, password hashing (Werkzeug)
- **Deployment**: Manus Cloud Platform

### Application Structure
```
lookman/
├── src/
│   ├── main.py                 # Flask application entry point
│   ├── models/                 # Database models
│   │   ├── __init__.py
│   │   ├── user.py            # User model and authentication
│   │   ├── borrower.py        # Borrower model
│   │   ├── loan.py            # Loan model with business logic
│   │   ├── payment.py         # Payment tracking model
│   │   ├── salary.py          # Salary calculation model
│   │   └── settings.py        # System settings model
│   ├── routes/                # API endpoints
│   │   ├── auth.py            # Authentication routes
│   │   ├── admin.py           # Admin management routes
│   │   ├── borrowers.py       # Borrower CRUD operations
│   │   ├── loans.py           # Loan management routes
│   │   ├── payments.py        # Payment tracking routes
│   │   ├── salary.py          # Salary calculation routes
│   │   ├── reports.py         # Reporting and analytics
│   │   └── automation.py      # Automation and scheduled tasks
│   ├── utils/                 # Utility functions
│   │   ├── __init__.py
│   │   └── automation.py      # Automation utilities
│   ├── static/                # Frontend assets
│   │   ├── index.html         # Main application interface
│   │   ├── style.css          # Custom styling
│   │   └── app.js             # Frontend JavaScript
│   └── database/              # Database files
│       └── app.db             # SQLite database
├── venv/                      # Python virtual environment
├── requirements.txt           # Python dependencies
└── test_app.py               # Application test suite
```

---

## Database Schema

### Core Models

#### User Model
```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='account_officer')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Borrower Model
```python
class Borrower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text)
    id_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Loan Model
```python
class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    borrower_id = db.Column(db.Integer, db.ForeignKey('borrower.id'), nullable=False)
    account_officer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    principal_amount = db.Column(db.Numeric(10, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)
    interest_amount = db.Column(db.Numeric(10, 2), nullable=False)
    expenses = db.Column(db.Numeric(10, 2), default=0.00)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    loan_duration_days = db.Column(db.Integer, nullable=False)
    daily_repayment = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='active')
    start_date = db.Column(db.Date, nullable=False)
    expected_end_date = db.Column(db.Date, nullable=False)
    actual_end_date = db.Column(db.Date)
```

#### Payment Model
```python
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    expected_amount = db.Column(db.Numeric(10, 2), nullable=False)
    actual_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_day = db.Column(db.Integer, nullable=False)
    is_weekend_adjusted = db.Column(db.Boolean, default=False)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.Text)
```

### Relationships
- User → Loans (one-to-many)
- Borrower → Loans (one-to-many)
- Loan → Payments (one-to-many)
- User → Payments (one-to-many, recorded_by)
- User → SalaryCalculations (one-to-many)

---

## API Endpoints

### Authentication (`/api/auth/`)
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /check-auth` - Check authentication status

### Admin Management (`/api/admin/`)
- `GET /users` - List all users
- `POST /users` - Create new user
- `PUT /users/<id>` - Update user
- `DELETE /users/<id>` - Delete user
- `GET /dashboard/stats` - Dashboard statistics

### Borrower Management (`/api/borrowers/`)
- `GET /` - List borrowers
- `POST /` - Create borrower
- `GET /<id>` - Get borrower details
- `PUT /<id>` - Update borrower
- `DELETE /<id>` - Delete borrower

### Loan Management (`/api/loans/`)
- `GET /` - List loans
- `POST /` - Create loan
- `GET /<id>` - Get loan details
- `PUT /<id>` - Update loan
- `DELETE /<id>` - Delete loan
- `GET /<id>/schedule` - Get payment schedule

### Payment Tracking (`/api/payments/`)
- `GET /` - List payments
- `POST /` - Record payment
- `GET /<id>` - Get payment details
- `PUT /<id>` - Update payment
- `DELETE /<id>` - Delete payment
- `GET /today` - Today's payments
- `GET /overdue` - Overdue payments

### Salary Management (`/api/salary/`)
- `GET /` - List salary calculations
- `POST /` - Create salary calculation
- `PUT /<id>` - Update salary calculation
- `DELETE /<id>` - Delete salary calculation
- `GET /performance/<user_id>` - User performance
- `GET /summary` - Salary summary
- `GET /income-statement` - Income statement

### Reports (`/api/reports/`)
- `GET /daily-collections` - Daily collections report
- `GET /outstanding-loans` - Outstanding loans report
- `GET /profit-loss` - Profit and loss report
- `GET /performance` - Performance report
- `GET /monthly-summary` - Monthly summary

### Automation (`/api/automation/`)
- `POST /daily-tasks` - Run daily automation
- `POST /monthly-tasks` - Run monthly automation
- `POST /update-loan-statuses` - Update loan statuses
- `POST /identify-overdue` - Identify overdue loans
- `GET /system-health` - System health check

---

## Business Logic

### Loan Calculations
```python
# Interest calculation
interest_amount = principal_amount * (interest_rate / 100)

# Total amount
total_amount = principal_amount + interest_amount + expenses

# Daily repayment
daily_repayment = total_amount / loan_duration_days

# Payment schedule (excludes weekends)
def generate_payment_schedule(start_date, duration_days):
    schedule = []
    current_date = start_date
    day_count = 1
    
    while day_count <= duration_days:
        # Skip weekends
        if current_date.weekday() < 5:  # Monday=0, Friday=4
            schedule.append({
                'day': day_count,
                'date': current_date,
                'amount': daily_repayment
            })
            day_count += 1
        current_date += timedelta(days=1)
    
    return schedule
```

### Salary Calculations
```python
# Commission calculation
commission_amount = total_collections * (commission_rate / 100)

# Total salary
total_salary = base_salary + commission_amount
```

### Outstanding Balance
```python
def get_outstanding_balance(loan):
    total_paid = sum(payment.actual_amount for payment in loan.payments)
    return loan.total_amount - total_paid
```

---

## Security Implementation

### Authentication
- Session-based authentication using Flask-Login
- Password hashing with Werkzeug security utilities
- Role-based access control (admin vs account_officer)

### Authorization Decorators
```python
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def account_officer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        if current_user.role not in ['admin', 'account_officer']:
            return jsonify({'error': 'Account officer access required'}), 403
        return f(*args, **kwargs)
    return decorated_function
```

### Data Validation
- Input validation on all API endpoints
- SQL injection prevention through SQLAlchemy ORM
- XSS protection through proper data sanitization
- CORS configuration for cross-origin requests

---

## Deployment Configuration

### Environment Setup
```python
# Flask configuration
app.config['SECRET_KEY'] = 'lookman-loan-management-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CORS configuration
CORS(app, supports_credentials=True)

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
```

### Production Deployment
- Deployed on Manus Cloud Platform
- HTTPS enabled by default
- Automatic scaling and load balancing
- Database persistence and backup

---

## Automation System

### Daily Automation Tasks
1. **Update Loan Statuses**: Check and update loan statuses based on payments
2. **Identify Overdue Loans**: Mark loans past their due date as overdue
3. **Create Payment Records**: Generate expected payment records for today
4. **Generate Daily Summary**: Create daily performance reports

### Monthly Automation Tasks
1. **Calculate Salaries**: Compute monthly salaries for all account officers
2. **Generate Monthly Reports**: Create comprehensive monthly summaries

### Automation Utilities
```python
class PaymentAutomation:
    @staticmethod
    def update_all_loan_statuses():
        # Update loan statuses based on payments and dates
        
    @staticmethod
    def identify_overdue_loans():
        # Mark overdue loans
        
    @staticmethod
    def auto_create_payment_records():
        # Create payment records for expected payments

class SalaryAutomation:
    @staticmethod
    def calculate_monthly_salaries(year, month):
        # Calculate salaries for all account officers
```

---

## Performance Optimization

### Database Optimization
- Proper indexing on frequently queried columns
- Efficient query patterns using SQLAlchemy
- Lazy loading for related objects
- Connection pooling

### Frontend Optimization
- Minified CSS and JavaScript
- Responsive design for mobile devices
- Efficient DOM manipulation
- AJAX for dynamic content loading

### Caching Strategy
- Session-based caching for user data
- Browser caching for static assets
- Database query optimization

---

## Monitoring and Logging

### System Health Monitoring
```python
@automation_bp.route('/system-health', methods=['GET'])
def system_health():
    # Check database connectivity
    # Monitor application performance
    # Return system status
```

### Error Handling
- Comprehensive error handling in all routes
- User-friendly error messages
- Logging of system errors and exceptions
- Graceful degradation for failed operations

### Backup and Recovery
- Automatic database backups (platform-managed)
- Data export capabilities through reports
- System state monitoring

---

## Development Setup

### Local Development
```bash
# Clone or download the application files
cd lookman

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

### Testing
```bash
# Run test suite
python test_app.py

# Manual testing
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Database Management
```python
# Initialize database
from src.main import app, db
with app.app_context():
    db.create_all()

# Create admin user
from src.models import User
admin = User(username='admin', full_name='System Administrator', role='admin')
admin.set_password('admin123')
db.session.add(admin)
db.session.commit()
```

---

## Maintenance and Updates

### Regular Maintenance Tasks
1. **Database Cleanup**: Remove old logs and temporary data
2. **Performance Monitoring**: Check system performance metrics
3. **Security Updates**: Keep dependencies updated
4. **Backup Verification**: Ensure backup systems are working

### Update Procedures
1. **Code Updates**: Deploy new features through the platform
2. **Database Migrations**: Handle schema changes carefully
3. **Configuration Changes**: Update system settings as needed
4. **Testing**: Thoroughly test all changes before deployment

### Troubleshooting Common Issues
1. **Database Lock Issues**: Restart application if SQLite locks occur
2. **Memory Issues**: Monitor memory usage and optimize queries
3. **Authentication Problems**: Check session configuration
4. **Performance Degradation**: Analyze slow queries and optimize

---

## Support and Contact

### Technical Support
- **Application URL**: https://60h5imce1zml.manus.space
- **Documentation**: This technical guide and user manual
- **Platform Support**: Manus Cloud Platform support

### Development Team
- **Primary Developer**: AI Assistant (Manus)
- **Technology Stack**: Python Flask, SQLAlchemy, Bootstrap
- **Development Date**: July 2025

---

*This technical documentation provides comprehensive information for system administrators, developers, and technical users of the Lookman Loan Management System.*

