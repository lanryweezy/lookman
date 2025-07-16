from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from user import db
# Model imports will be resolved through circular imports
from settings import SystemSetting
from auth import account_officer_required
from datetime import datetime, date
from decimal import Decimal

loans_bp = Blueprint('loans', __name__)

@loans_bp.route('/', methods=['GET'])
@login_required
@account_officer_required
def get_loans():
    """Get all loans (filtered by user role and optional filters)"""
    try:
        # Get query parameters for filtering
        status = request.args.get('status')
        borrower_id = request.args.get('borrower_id')
        
        # Base query
        query = Loan.query
        
        # Filter by user role
        if not current_user.is_admin():
            query = query.filter_by(account_officer_id=current_user.id)
        
        # Apply additional filters
        if status:
            query = query.filter_by(status=status)
        
        if borrower_id:
            query = query.filter_by(borrower_id=borrower_id)
        
        loans = query.order_by(Loan.created_at.desc()).all()
        
        return jsonify({
            'loans': [loan.to_dict() for loan in loans]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@loans_bp.route('/', methods=['POST'])
@login_required
@account_officer_required
def create_loan():
    """Create a new loan"""
    try:
        data = request.get_json()
        borrower_id = data.get('borrower_id')
        principal_amount = data.get('principal_amount')
        interest_rate = data.get('interest_rate')
        expenses = data.get('expenses', 0)
        loan_duration_days = data.get('loan_duration_days')
        start_date_str = data.get('start_date')
        
        # Validation
        if not borrower_id:
            return jsonify({'error': 'Borrower ID is required'}), 400
        
        if not principal_amount or principal_amount <= 0:
            return jsonify({'error': 'Principal amount must be greater than 0'}), 400
        
        if not start_date_str:
            return jsonify({'error': 'Start date is required'}), 400
        
        # Validate borrower exists and user has permission
        from borrowers import Borrower
        borrower = Borrower.query.get_or_404(borrower_id)
        if not current_user.is_admin() and borrower.created_by != current_user.id:
            return jsonify({'error': 'Access denied to this borrower'}), 403
        
        # Check for active loans for this borrower
        active_loan = Loan.query.filter_by(borrower_id=borrower_id, status='active').first()
        if active_loan:
            return jsonify({'error': 'Borrower already has an active loan'}), 400
        
        # Parse start date
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid start date format. Use YYYY-MM-DD'}), 400
        
        # Get default values from system settings if not provided
        if interest_rate is None:
            interest_rate = float(SystemSetting.get_setting('default_interest_rate', '10.00'))
        
        if loan_duration_days is None:
            loan_duration_days = int(SystemSetting.get_setting('default_loan_duration', '15'))
        
        # Create new loan
        new_loan = Loan(
            borrower_id=borrower_id,
            account_officer_id=current_user.id,
            principal_amount=Decimal(str(principal_amount)),
            interest_rate=Decimal(str(interest_rate)),
            expenses=Decimal(str(expenses)),
            loan_duration_days=loan_duration_days,
            start_date=start_date
        )
        
        # Add optional fields
        for field in data:
            if hasattr(new_loan, field) and field not in ['borrower_id', 'principal_amount', 'interest_rate', 'expenses', 'loan_duration_days', 'start_date']:
                setattr(new_loan, field, data[field])

        # Calculate loan amounts
        new_loan.calculate_interest()
        new_loan.calculate_total_amount()
        new_loan.calculate_daily_repayment()
        new_loan.calculate_expected_end_date()
        
        db.session.add(new_loan)
        db.session.commit()
        
        return jsonify({
            'message': 'Loan created successfully',
            'loan': new_loan.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@loans_bp.route('/<int:loan_id>', methods=['GET'])
@login_required
@account_officer_required
def get_loan(loan_id):
    """Get a specific loan"""
    try:
        loan = Loan.query.get_or_404(loan_id)
        
        # Check permissions
        if not current_user.is_admin() and loan.account_officer_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'loan': loan.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@loans_bp.route('/<int:loan_id>', methods=['PUT'])
@login_required
@account_officer_required
def update_loan(loan_id):
    """Update a loan"""
    try:
        loan = Loan.query.get_or_404(loan_id)
        
        # Check permissions
        if not current_user.is_admin() and loan.account_officer_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Only allow updates to active loans
        if loan.status != 'active':
            return jsonify({'error': 'Can only update active loans'}), 400
        
        data = request.get_json()
        
        # Update allowed fields
        if 'expenses' in data:
            loan.expenses = Decimal(str(data['expenses']))
        
        if 'interest_rate' in data:
            loan.interest_rate = Decimal(str(data['interest_rate']))
            loan.calculate_interest()
        
        # Recalculate amounts if any financial data changed
        if 'expenses' in data or 'interest_rate' in data:
            loan.calculate_total_amount()
            loan.calculate_daily_repayment()
        
        loan.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Loan updated successfully',
            'loan': loan.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@loans_bp.route('/<int:loan_id>/schedule', methods=['GET'])
@login_required
@account_officer_required
def get_loan_schedule(loan_id):
    """Get payment schedule for a loan"""
    try:
        loan = Loan.query.get_or_404(loan_id)
        
        # Check permissions
        if not current_user.is_admin() and loan.account_officer_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        schedule = loan.get_payment_schedule()
        
        return jsonify({
            'loan_id': loan_id,
            'schedule': schedule
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@loans_bp.route('/<int:loan_id>/status', methods=['PUT'])
@login_required
@account_officer_required
def update_loan_status(loan_id):
    """Update loan status"""
    try:
        loan = Loan.query.get_or_404(loan_id)
        
        # Check permissions
        if not current_user.is_admin() and loan.account_officer_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['active', 'completed', 'overdue', 'defaulted']:
            return jsonify({'error': 'Invalid status'}), 400
        
        loan.status = new_status
        
        # Set actual end date if completing the loan
        if new_status == 'completed' and not loan.actual_end_date:
            loan.actual_end_date = date.today()
        
        loan.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Loan status updated successfully',
            'loan': loan.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@loans_bp.route('/summary', methods=['GET'])
@login_required
@account_officer_required
def get_loans_summary():
    """Get loans summary statistics"""
    try:
        # Base query filtered by user role
        if current_user.is_admin():
            loans = Loan.query.all()
        else:
            loans = Loan.query.filter_by(account_officer_id=current_user.id).all()
        
        # Calculate summary statistics
        total_loans = len(loans)
        active_loans = len([loan for loan in loans if loan.status == 'active'])
        completed_loans = len([loan for loan in loans if loan.status == 'completed'])
        overdue_loans = len([loan for loan in loans if loan.status == 'overdue'])
        defaulted_loans = len([loan for loan in loans if loan.status == 'defaulted'])
        
        total_principal = sum(loan.principal_amount for loan in loans)
        total_expected = sum(loan.total_amount for loan in loans)
        total_collected = sum(loan.get_total_payments() for loan in loans)
        total_outstanding = sum(loan.get_outstanding_balance() for loan in loans if loan.status == 'active')
        
        return jsonify({
            'summary': {
                'total_loans': total_loans,
                'active_loans': active_loans,
                'completed_loans': completed_loans,
                'overdue_loans': overdue_loans,
                'defaulted_loans': defaulted_loans,
                'total_principal': float(total_principal),
                'total_expected': float(total_expected),
                'total_collected': float(total_collected),
                'total_outstanding': float(total_outstanding)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Model Definition
class Loan(db.Model):
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    borrower_id = db.Column(db.Integer, db.ForeignKey('borrowers.id'), nullable=False)
    account_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    principal_amount = db.Column(db.Numeric(10, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), default=0.00)
    interest_amount = db.Column(db.Numeric(10, 2), default=0.00)
    expenses = db.Column(db.Numeric(10, 2), default=0.00)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    daily_repayment = db.Column(db.Numeric(10, 2), nullable=False)
    loan_duration_days = db.Column(db.Integer, default=15)
    start_date = db.Column(db.Date, nullable=False)
    expected_end_date = db.Column(db.Date, nullable=False)
    actual_end_date = db.Column(db.Date)
    status = db.Column(db.Enum('active', 'completed', 'overdue', 'defaulted', name='loan_status'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Loan Application Details
    loan_purpose = db.Column(db.String(100))
    loan_term = db.Column(db.Integer)  # in months

    # Collateral Information
    has_collateral = db.Column(db.Boolean, default=False)
    collateral_type = db.Column(db.String(50))
    collateral_value = db.Column(db.Numeric(15, 2))
    collateral_description = db.Column(db.Text)

    # Guarantor Information
    guarantor_name = db.Column(db.String(100))
    guarantor_phone = db.Column(db.String(20))
    guarantor_address = db.Column(db.Text)
    guarantor_relationship = db.Column(db.String(50))

    # Relationships
    payments = db.relationship('Payment', backref='loan', lazy=True, cascade='all, delete-orphan')
    
    def calculate_interest(self):
        """Calculate interest amount"""
        self.interest_amount = (self.principal_amount * self.interest_rate) / 100
    
    def calculate_total_amount(self):
        """Calculate total amount to be repaid"""
        self.total_amount = self.principal_amount + self.interest_amount + self.expenses
    
    def calculate_daily_repayment(self):
        """Calculate daily repayment amount"""
        self.daily_repayment = self.total_amount / self.loan_duration_days
    
    def calculate_expected_end_date(self):
        """Calculate expected end date"""
        from datetime import timedelta
        self.expected_end_date = self.start_date + timedelta(days=self.loan_duration_days - 1)
    
    def get_payment_schedule(self):
        """Get payment schedule for this loan"""
        from datetime import timedelta
        schedule = []
        current_date = self.start_date
        
        for day in range(1, self.loan_duration_days + 1):
            # Skip weekends by moving to next business day
            while current_date.weekday() >= 5:  # Saturday=5, Sunday=6
                current_date += timedelta(days=1)
            
            schedule.append({
                'day': day,
                'date': current_date,
                'expected_amount': float(self.daily_repayment)
            })
            
            current_date += timedelta(days=1)
        
        return schedule
    
    def get_total_payments(self):
        """Get total payments made for this loan"""
        return sum(payment.actual_amount for payment in self.payments)
    
    def get_outstanding_balance(self):
        """Get outstanding balance"""
        return self.total_amount - self.get_total_payments()
    
    def update_status(self):
        """Update loan status based on payments and dates"""
        from datetime import date
        today = date.today()
        
        total_paid = self.get_total_payments()
        
        # Check if loan is completed
        if total_paid >= self.total_amount:
            self.status = 'completed'
            if not self.actual_end_date:
                self.actual_end_date = today
        elif today > self.expected_end_date:
            self.status = 'overdue'
        else:
            self.status = 'active'
    
    def is_overdue(self):
        """Check if loan is overdue"""
        from datetime import date
        return date.today() > self.expected_end_date and self.status != 'completed'
    
    def to_dict(self):
        return {
            'id': self.id,
            'borrower_id': self.borrower_id,
            'account_officer_id': self.account_officer_id,
            'principal_amount': float(self.principal_amount),
            'interest_rate': float(self.interest_rate),
            'interest_amount': float(self.interest_amount),
            'expenses': float(self.expenses),
            'total_amount': float(self.total_amount),
            'daily_repayment': float(self.daily_repayment),
            'loan_duration_days': self.loan_duration_days,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'expected_end_date': self.expected_end_date.isoformat() if self.expected_end_date else None,
            'actual_end_date': self.actual_end_date.isoformat() if self.actual_end_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'total_payments': float(self.get_total_payments()),
            'outstanding_balance': float(self.get_outstanding_balance())
        }
    
    def __repr__(self):
        return f'<Loan {self.id} - {self.borrower.name if self.borrower else "Unknown"} - {self.status}>'
