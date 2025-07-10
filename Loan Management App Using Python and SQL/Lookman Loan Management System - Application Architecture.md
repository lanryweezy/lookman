# Lookman Loan Management System - Application Architecture

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite (for development) / PostgreSQL (for production)
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login with session management
- **Frontend**: HTML5, CSS3, JavaScript (with Bootstrap for responsive design)
- **Password Hashing**: Werkzeug security utilities
- **Date/Time Handling**: Python datetime and dateutil

## Application Structure

```
lookman/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── models/
│   ├── __init__.py
│   ├── user.py          # User model
│   ├── borrower.py      # Borrower model
│   ├── loan.py          # Loan model
│   ├── payment.py       # Payment model
│   ├── salary.py        # Salary calculation model
│   └── settings.py      # System settings model
├── routes/
│   ├── __init__.py
│   ├── auth.py          # Authentication routes
│   ├── admin.py         # Admin routes
│   ├── loans.py         # Loan management routes
│   ├── payments.py      # Payment routes
│   ├── reports.py       # Reporting routes
│   └── api.py           # API endpoints
├── templates/
│   ├── base.html        # Base template
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── users.html
│   │   ├── settings.html
│   │   └── reports.html
│   ├── loans/
│   │   ├── list.html
│   │   ├── create.html
│   │   ├── edit.html
│   │   └── view.html
│   └── payments/
│       ├── record.html
│       └── history.html
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── images/
└── utils/
    ├── __init__.py
    ├── calculations.py   # Business logic calculations
    ├── helpers.py       # Helper functions
    └── decorators.py    # Custom decorators
```

## Core Features and API Endpoints

### Authentication
- **POST** `/auth/login` - User login
- **POST** `/auth/logout` - User logout
- **GET** `/auth/profile` - User profile

### Admin Management
- **GET** `/admin/dashboard` - Admin dashboard
- **GET** `/admin/users` - List all users
- **POST** `/admin/users` - Create new user
- **PUT** `/admin/users/<id>` - Update user
- **DELETE** `/admin/users/<id>` - Delete user
- **GET** `/admin/settings` - System settings
- **POST** `/admin/settings` - Update settings

### Borrower Management
- **GET** `/borrowers` - List borrowers
- **POST** `/borrowers` - Create new borrower
- **GET** `/borrowers/<id>` - Get borrower details
- **PUT** `/borrowers/<id>` - Update borrower
- **DELETE** `/borrowers/<id>` - Delete borrower

### Loan Management
- **GET** `/loans` - List loans (filtered by user role)
- **POST** `/loans` - Create new loan
- **GET** `/loans/<id>` - Get loan details
- **PUT** `/loans/<id>` - Update loan
- **DELETE** `/loans/<id>` - Delete loan
- **GET** `/loans/<id>/schedule` - Get payment schedule

### Payment Management
- **GET** `/payments` - List payments
- **POST** `/payments` - Record new payment
- **GET** `/payments/<id>` - Get payment details
- **PUT** `/payments/<id>` - Update payment
- **GET** `/loans/<loan_id>/payments` - Get payments for a loan

### Reporting
- **GET** `/reports/daily-collections` - Daily collection report
- **GET** `/reports/outstanding-loans` - Outstanding loans report
- **GET** `/reports/salary-calculations` - Salary calculation report
- **GET** `/reports/profit-loss` - Profit and loss report

### API Endpoints (JSON responses)
- **GET** `/api/loans/summary` - Loan summary statistics
- **GET** `/api/payments/today` - Today's payments
- **GET** `/api/dashboard/stats` - Dashboard statistics

## User Roles and Permissions

### Admin
- Full access to all features
- User management (create, edit, delete users)
- System settings management
- View all loans and payments
- Generate all reports
- Salary calculations

### Account Officer
- Create and manage borrowers
- Create and manage loans assigned to them
- Record payments for their loans
- View their own performance reports
- View their salary calculations

## Business Logic Components

### Loan Calculations
- **calculate_total_amount()**: Principal + Interest + Expenses
- **calculate_daily_repayment()**: Total amount / Loan duration
- **calculate_interest()**: Principal × Interest rate
- **generate_payment_schedule()**: Create expected payment dates

### Payment Processing
- **record_payment()**: Record actual payment with validation
- **calculate_outstanding()**: Calculate remaining balance
- **check_overdue()**: Identify overdue payments
- **weekend_adjustment()**: Handle weekend payment adjustments

### Salary Calculations
- **calculate_commission()**: Based on collections and commission rate
- **calculate_total_salary()**: Base salary + Commission
- **generate_salary_report()**: Monthly salary breakdown

### Reporting
- **daily_collections_report()**: Daily payment collections
- **outstanding_loans_report()**: Loans with outstanding balances
- **profit_loss_report()**: Income vs expenses analysis
- **performance_report()**: Account officer performance

## Security Features

1. **Password Hashing**: Using Werkzeug's password hashing
2. **Session Management**: Flask-Login for user sessions
3. **Role-based Access Control**: Decorator-based permission checking
4. **Input Validation**: Server-side validation for all inputs
5. **CSRF Protection**: Cross-site request forgery protection

## Database Configuration

### Development
- SQLite database for easy setup and testing
- Database file: `lookman.db`

### Production
- PostgreSQL for better performance and scalability
- Connection pooling and proper indexing

## Deployment Considerations

1. **Environment Variables**: For sensitive configuration
2. **CORS Configuration**: Allow cross-origin requests
3. **Static File Serving**: Proper static file handling
4. **Error Handling**: Comprehensive error handling and logging
5. **Database Migrations**: SQLAlchemy-Migrate for schema updates

