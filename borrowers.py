from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from user import db
# Model imports will be resolved through circular imports
from auth import account_officer_required
from datetime import datetime

borrowers_bp = Blueprint('borrowers', __name__)

@borrowers_bp.route('/', methods=['GET'])
@login_required
@account_officer_required
def get_borrowers():
    """Get all borrowers (filtered by user role)"""
    try:
        # Admin can see all borrowers, account officers see only their own
        if current_user.is_admin():
            borrowers = Borrower.query.all()
        else:
            borrowers = Borrower.query.filter_by(created_by=current_user.id).all()
        
        return jsonify({
            'borrowers': [borrower.to_dict() for borrower in borrowers]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@borrowers_bp.route('/', methods=['POST'])
@login_required
@account_officer_required
def create_borrower():
    """Create a new borrower"""
    try:
        data = request.get_json()
        name = data.get('name')
        
        # Validation
        if not name:
            return jsonify({'error': 'Borrower name is required'}), 400
        
        if len(name.strip()) < 2:
            return jsonify({'error': 'Borrower name must be at least 2 characters long'}), 400
        
        # Create new borrower
        new_borrower = Borrower(
            name=name.strip(),
            created_by=current_user.id
        )
        
        # Update optional fields
        for field in data:
            if hasattr(new_borrower, field) and field not in ['name', 'created_by']:
                setattr(new_borrower, field, data[field])

        db.session.add(new_borrower)
        db.session.commit()
        
        return jsonify({
            'message': 'Borrower created successfully',
            'borrower': new_borrower.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@borrowers_bp.route('/<int:borrower_id>', methods=['GET'])
@login_required
@account_officer_required
def get_borrower(borrower_id):
    """Get a specific borrower"""
    try:
        borrower = Borrower.query.get_or_404(borrower_id)
        
        # Check permissions
        if not current_user.is_admin() and borrower.created_by != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'borrower': borrower.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@borrowers_bp.route('/<int:borrower_id>', methods=['PUT'])
@login_required
@account_officer_required
def update_borrower(borrower_id):
    """Update a borrower"""
    try:
        borrower = Borrower.query.get_or_404(borrower_id)
        
        # Check permissions
        if not current_user.is_admin() and borrower.created_by != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update fields if provided
        for field in data:
            if hasattr(borrower, field) and field not in ['id', 'created_by', 'created_at']:
                setattr(borrower, field, data[field])
        
        borrower.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Borrower updated successfully',
            'borrower': borrower.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@borrowers_bp.route('/<int:borrower_id>', methods=['DELETE'])
@login_required
@account_officer_required
def delete_borrower(borrower_id):
    """Delete a borrower"""
    try:
        borrower = Borrower.query.get_or_404(borrower_id)
        
        # Check permissions
        if not current_user.is_admin() and borrower.created_by != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if borrower has active loans
        active_loans = Loan.query.filter_by(borrower_id=borrower_id, status='active').count()
        if active_loans > 0:
            return jsonify({'error': f'Cannot delete borrower with {active_loans} active loans'}), 400
        
        db.session.delete(borrower)
        db.session.commit()
        
        return jsonify({'message': 'Borrower deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@borrowers_bp.route('/<int:borrower_id>/loans', methods=['GET'])
@login_required
@account_officer_required
def get_borrower_loans(borrower_id):
    """Get all loans for a specific borrower"""
    try:
        borrower = Borrower.query.get_or_404(borrower_id)
        
        # Check permissions
        if not current_user.is_admin() and borrower.created_by != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        loans = Loan.query.filter_by(borrower_id=borrower_id).all()
        
        return jsonify({
            'borrower': borrower.to_dict(),
            'loans': [loan.to_dict() for loan in loans]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Model Definition
class Borrower(db.Model):
    __tablename__ = 'borrowers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Personal Information
    date_of_birth = db.Column(db.Date)
    email = db.Column(db.String(100))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    country = db.Column(db.String(50), default='Nigeria')
    marital_status = db.Column(db.String(50))

    # Identification
    bvn = db.Column(db.String(11))  # Bank Verification Number
    nin = db.Column(db.String(11))  # National Identification Number
    primary_id_type = db.Column(db.String(50))
    primary_id_number = db.Column(db.String(50))

    # Employment Information
    employment_type = db.Column(db.String(50))
    employer_name = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    work_address = db.Column(db.Text)
    monthly_income = db.Column(db.Numeric(15, 2))
    employment_start_date = db.Column(db.Date)

    # Business Information (for self-employed)
    business_name = db.Column(db.String(100))
    business_registration_number = db.Column(db.String(50))  # CAC number
    business_address = db.Column(db.Text)
    business_type = db.Column(db.String(100))
    annual_revenue = db.Column(db.Numeric(15, 2))

    # Banking Information
    bank_name = db.Column(db.String(100))
    account_number = db.Column(db.String(10))
    account_name = db.Column(db.String(100))
    account_type = db.Column(db.String(20))

    # Relationships
    loans = db.relationship('Loan', backref='borrower', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'email': self.email,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'marital_status': self.marital_status,
            'bvn': self.bvn,
            'nin': self.nin,
            'primary_id_type': self.primary_id_type,
            'primary_id_number': self.primary_id_number,
            'employment_type': self.employment_type,
            'employer_name': self.employer_name,
            'job_title': self.job_title,
            'work_address': self.work_address,
            'monthly_income': float(self.monthly_income) if self.monthly_income else None,
            'employment_start_date': self.employment_start_date.isoformat() if self.employment_start_date else None,
            'business_name': self.business_name,
            'business_registration_number': self.business_registration_number,
            'business_address': self.business_address,
            'business_type': self.business_type,
            'annual_revenue': float(self.annual_revenue) if self.annual_revenue else None,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'account_name': self.account_name,
            'account_type': self.account_type,
        }
    
    def __repr__(self):
        return f'<Borrower {self.name}>'
