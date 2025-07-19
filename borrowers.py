from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from user import db
from auth import account_officer_required
from datetime import datetime
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

borrowers_bp = Blueprint('borrowers', __name__)

@borrowers_bp.route('/', methods=['GET'])
@login_required
@account_officer_required
def get_borrowers():
    """Get all borrowers (filtered by user role)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        query = Borrower.query

        # Filter by user role
        if not current_user.is_admin():
            query = query.filter_by(created_by=current_user.id)

        # Search
        search_term = request.args.get('search')
        if search_term:
            query = query.filter(
                Borrower.name.ilike(f'%{search_term}%') |
                Borrower.phone.ilike(f'%{search_term}%')
            )

        borrowers = query.paginate(page=page, per_page=per_page)
        
        borrower_schema = BorrowerSchema(many=True)
        return jsonify({
            'borrowers': borrower_schema.dump(borrowers.items),
            'total_pages': borrowers.pages,
            'current_page': borrowers.page,
            'total_items': borrowers.total
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
        
        borrower_schema = BorrowerSchema()
        return jsonify({
            'message': 'Borrower created successfully',
            'borrower': borrower_schema.dump(new_borrower)
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
        
        borrower_schema = BorrowerSchema()
        return jsonify({
            'borrower': borrower_schema.dump(borrower)
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
        
        borrower_schema = BorrowerSchema()
        return jsonify({
            'message': 'Borrower updated successfully',
            'borrower': borrower_schema.dump(borrower)
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
        from loans import Loan
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
        
        from loans import Loan, LoanSchema
        loans = Loan.query.filter_by(borrower_id=borrower_id).all()
        
        borrower_schema = BorrowerSchema()
        loan_schema = LoanSchema(many=True)
        return jsonify({
            'borrower': borrower_schema.dump(borrower),
            'loans': loan_schema.dump(loans)
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
    
    def __repr__(self):
        return f'<Borrower {self.name}>'

from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field

class BorrowerSchema(SQLAlchemySchema):
    class Meta:
        model = Borrower
        load_instance = True

    id = auto_field(dump_only=True)
    name = auto_field()
    phone = auto_field()
    address = auto_field()
    created_by = auto_field()
    created_at = auto_field()
    updated_at = auto_field()
    date_of_birth = auto_field()
    email = auto_field()
    city = auto_field()
    state = auto_field()
    country = auto_field()
    marital_status = auto_field()
    bvn = auto_field()
    nin = auto_field()
    primary_id_type = auto_field()
    primary_id_number = auto_field()
    employment_type = auto_field()
    employer_name = auto_field()
    job_title = auto_field()
    work_address = auto_field()
    monthly_income = auto_field()
    employment_start_date = auto_field()
    business_name = auto_field()
    business_registration_number = auto_field()
    business_address = auto_field()
    business_type = auto_field()
    annual_revenue = auto_field()
    bank_name = auto_field()
    account_number = auto_field()
    account_name = auto_field()
    account_type = auto_field()
