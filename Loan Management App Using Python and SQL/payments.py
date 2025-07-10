from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from user import db
# Model imports will be resolved through circular imports
from auth import account_officer_required
from datetime import datetime, date
from decimal import Decimal

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/', methods=['GET'])
@login_required
@account_officer_required
def get_payments():
    """Get all payments (filtered by user role and optional filters)"""
    try:
        # Get query parameters for filtering
        loan_id = request.args.get('loan_id')
        payment_date_str = request.args.get('payment_date')
        
        # Base query
        query = Payment.query.join(Loan)
        
        # Filter by user role
        if not current_user.is_admin():
            query = query.filter(Loan.account_officer_id == current_user.id)
        
        # Apply additional filters
        if loan_id:
            query = query.filter(Payment.loan_id == loan_id)
        
        if payment_date_str:
            try:
                payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
                query = query.filter(Payment.payment_date == payment_date)
            except ValueError:
                return jsonify({'error': 'Invalid payment date format. Use YYYY-MM-DD'}), 400
        
        payments = query.order_by(Payment.payment_date.desc()).all()
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/', methods=['POST'])
@login_required
@account_officer_required
def record_payment():
    """Record a new payment"""
    try:
        data = request.get_json()
        loan_id = data.get('loan_id')
        actual_amount = data.get('actual_amount')
        payment_date_str = data.get('payment_date')
        payment_day = data.get('payment_day')
        notes = data.get('notes')
        
        # Validation
        if not loan_id:
            return jsonify({'error': 'Loan ID is required'}), 400
        
        if actual_amount is None or actual_amount < 0:
            return jsonify({'error': 'Payment amount must be 0 or greater'}), 400
        
        if not payment_date_str:
            return jsonify({'error': 'Payment date is required'}), 400
        
        if not payment_day or payment_day < 1:
            return jsonify({'error': 'Payment day must be 1 or greater'}), 400
        
        # Validate loan exists and user has permission
        loan = Loan.query.get_or_404(loan_id)
        if not current_user.is_admin() and loan.account_officer_id != current_user.id:
            return jsonify({'error': 'Access denied to this loan'}), 403
        
        # Parse payment date
        try:
            payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid payment date format. Use YYYY-MM-DD'}), 400
        
        # Check if payment already exists for this loan and day
        existing_payment = Payment.query.filter_by(
            loan_id=loan_id, 
            payment_day=payment_day
        ).first()
        
        if existing_payment:
            return jsonify({'error': f'Payment for day {payment_day} already exists'}), 400
        
        # Calculate expected amount (daily repayment)
        expected_amount = loan.daily_repayment
        
        # Check for weekend adjustment
        is_weekend_adjusted = payment_date.weekday() >= 5  # Saturday=5, Sunday=6
        
        # Create new payment
        new_payment = Payment(
            loan_id=loan_id,
            payment_date=payment_date,
            expected_amount=expected_amount,
            actual_amount=Decimal(str(actual_amount)),
            payment_day=payment_day,
            is_weekend_adjusted=is_weekend_adjusted,
            recorded_by=current_user.id,
            notes=notes.strip() if notes else None
        )
        
        db.session.add(new_payment)
        
        # Update loan status based on payments
        loan.update_status()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Payment recorded successfully',
            'payment': new_payment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/<int:payment_id>', methods=['GET'])
@login_required
@account_officer_required
def get_payment(payment_id):
    """Get a specific payment"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        # Check permissions
        if not current_user.is_admin() and payment.loan.account_officer_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'payment': payment.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/<int:payment_id>', methods=['PUT'])
@login_required
@account_officer_required
def update_payment(payment_id):
    """Update a payment"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        # Check permissions
        if not current_user.is_admin() and payment.loan.account_officer_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update allowed fields
        if 'actual_amount' in data:
            if data['actual_amount'] < 0:
                return jsonify({'error': 'Payment amount must be 0 or greater'}), 400
            payment.actual_amount = Decimal(str(data['actual_amount']))
        
        if 'notes' in data:
            payment.notes = data['notes'].strip() if data['notes'] else None
        
        payment.updated_at = datetime.utcnow()
        
        # Update loan status based on updated payments
        payment.loan.update_status()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Payment updated successfully',
            'payment': payment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/<int:payment_id>', methods=['DELETE'])
@login_required
@account_officer_required
def delete_payment(payment_id):
    """Delete a payment"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        # Check permissions
        if not current_user.is_admin() and payment.loan.account_officer_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        loan = payment.loan
        
        db.session.delete(payment)
        
        # Update loan status after deleting payment
        loan.update_status()
        
        db.session.commit()
        
        return jsonify({'message': 'Payment deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/today', methods=['GET'])
@login_required
@account_officer_required
def get_today_payments():
    """Get today's payments"""
    try:
        today = date.today()
        
        # Base query
        query = Payment.query.join(Loan).filter(Payment.payment_date == today)
        
        # Filter by user role
        if not current_user.is_admin():
            query = query.filter(Loan.account_officer_id == current_user.id)
        
        payments = query.order_by(Payment.created_at.desc()).all()
        
        # Calculate summary
        total_expected = sum(payment.expected_amount for payment in payments)
        total_collected = sum(payment.actual_amount for payment in payments)
        
        return jsonify({
            'date': today.isoformat(),
            'payments': [payment.to_dict() for payment in payments],
            'summary': {
                'total_payments': len(payments),
                'total_expected': float(total_expected),
                'total_collected': float(total_collected),
                'collection_rate': float(total_collected / total_expected * 100) if total_expected > 0 else 0
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/overdue', methods=['GET'])
@login_required
@account_officer_required
def get_overdue_payments():
    """Get overdue payments (expected payments not made)"""
    try:
        today = date.today()
        
        # Get all active loans
        query = Loan.query.filter_by(status='active')
        
        # Filter by user role
        if not current_user.is_admin():
            query = query.filter_by(account_officer_id=current_user.id)
        
        active_loans = query.all()
        overdue_info = []
        
        for loan in active_loans:
            # Get payment schedule
            schedule = loan.get_payment_schedule()
            
            for day_info in schedule:
                payment_date = day_info['date']
                payment_day = day_info['day']
                
                # Check if this payment date has passed
                if payment_date < today:
                    # Check if payment was made
                    payment = Payment.query.filter_by(
                        loan_id=loan.id,
                        payment_day=payment_day
                    ).first()
                    
                    if not payment or payment.actual_amount < payment.expected_amount:
                        overdue_info.append({
                            'loan_id': loan.id,
                            'borrower_name': loan.borrower.name,
                            'payment_day': payment_day,
                            'expected_date': payment_date.isoformat(),
                            'expected_amount': float(loan.daily_repayment),
                            'actual_amount': float(payment.actual_amount) if payment else 0,
                            'days_overdue': (today - payment_date).days
                        })
        
        return jsonify({
            'overdue_payments': overdue_info,
            'total_overdue': len(overdue_info)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Model Definition
class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    expected_amount = db.Column(db.Numeric(10, 2), nullable=False)
    actual_amount = db.Column(db.Numeric(10, 2), default=0.00)
    payment_day = db.Column(db.Integer, nullable=False)
    is_weekend_adjusted = db.Column(db.Boolean, default=False)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'loan_id': self.loan_id,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'expected_amount': float(self.expected_amount),
            'actual_amount': float(self.actual_amount),
            'payment_day': self.payment_day,
            'is_weekend_adjusted': self.is_weekend_adjusted,
            'recorded_by': self.recorded_by,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Payment {self.id} - Loan {self.loan_id} - Day {self.payment_day}>'
