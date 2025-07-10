from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from user import db
from datetime import datetime
from enum import Enum
import json

profile_bp = Blueprint('profile', __name__)

class VerificationStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class LoanPurpose(Enum):
    DEBT_CONSOLIDATION = "debt_consolidation"
    HOME_IMPROVEMENT = "home_improvement"
    EDUCATION = "education"
    BUSINESS = "business"
    PERSONAL = "personal"
    MEDICAL = "medical"
    EMERGENCY = "emergency"

class EmploymentType(Enum):
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"
    RETIRED = "retired"
    STUDENT = "student"

class MaritalStatus(Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"

class IdentificationType(Enum):
    NIN = "nin"
    VOTERS_CARD = "voters_card"
    DRIVERS_LICENSE = "drivers_license"
    INTERNATIONAL_PASSPORT = "international_passport"

class BorrowerProfile(db.Model):
    __tablename__ = 'borrower_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    borrower_id = db.Column(db.Integer, db.ForeignKey('borrowers.id'), nullable=False, unique=True)
    
    # Personal Information
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    country = db.Column(db.String(50), default='Nigeria')
    marital_status = db.Column(db.Enum(MaritalStatus))
    
    # Identification
    bvn = db.Column(db.String(11))  # Bank Verification Number
    nin = db.Column(db.String(11))  # National Identification Number
    primary_id_type = db.Column(db.Enum(IdentificationType))
    primary_id_number = db.Column(db.String(50))
    
    # Employment Information
    employment_type = db.Column(db.Enum(EmploymentType))
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
    
    # Verification Status
    profile_verification_status = db.Column(db.Enum(VerificationStatus), default=VerificationStatus.PENDING)
    bvn_verification_status = db.Column(db.Enum(VerificationStatus), default=VerificationStatus.PENDING)
    id_verification_status = db.Column(db.Enum(VerificationStatus), default=VerificationStatus.PENDING)
    employment_verification_status = db.Column(db.Enum(VerificationStatus), default=VerificationStatus.PENDING)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    borrower = db.relationship('Borrower', backref='profile', lazy=True)
    documents = db.relationship('ProfileDocument', backref='profile', lazy=True, cascade='all, delete-orphan')
    loan_applications = db.relationship('LoanApplication', backref='profile', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'borrower_id': self.borrower_id,
            'full_name': self.full_name,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'phone_number': self.phone_number,
            'email': self.email,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'marital_status': self.marital_status.value if self.marital_status else None,
            'bvn': self.bvn,
            'nin': self.nin,
            'primary_id_type': self.primary_id_type.value if self.primary_id_type else None,
            'primary_id_number': self.primary_id_number,
            'employment_type': self.employment_type.value if self.employment_type else None,
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
            'profile_verification_status': self.profile_verification_status.value if self.profile_verification_status else None,
            'bvn_verification_status': self.bvn_verification_status.value if self.bvn_verification_status else None,
            'id_verification_status': self.id_verification_status.value if self.id_verification_status else None,
            'employment_verification_status': self.employment_verification_status.value if self.employment_verification_status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'documents': [doc.to_dict() for doc in self.documents] if self.documents else []
        }

class ProfileDocument(db.Model):
    __tablename__ = 'profile_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('borrower_profiles.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # id_document, utility_bill, salary_slip, etc.
    document_name = db.Column(db.String(100), nullable=False)
    document_path = db.Column(db.String(255))  # For file uploads
    document_data = db.Column(db.Text)  # For browser captured data
    verification_status = db.Column(db.Enum(VerificationStatus), default=VerificationStatus.PENDING)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'document_type': self.document_type,
            'document_name': self.document_name,
            'document_path': self.document_path,
            'document_data': self.document_data,
            'verification_status': self.verification_status.value if self.verification_status else None,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }

class LoanApplication(db.Model):
    __tablename__ = 'loan_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('borrower_profiles.id'), nullable=False)
    
    # Loan Details
    loan_purpose = db.Column(db.Enum(LoanPurpose), nullable=False)
    loan_amount = db.Column(db.Numeric(15, 2), nullable=False)
    loan_term = db.Column(db.Integer, nullable=False)  # in months
    interest_rate = db.Column(db.Numeric(5, 2))
    
    # Collateral Information
    has_collateral = db.Column(db.Boolean, default=False)
    collateral_type = db.Column(db.String(50))  # land, vehicle, equipment, etc.
    collateral_value = db.Column(db.Numeric(15, 2))
    collateral_description = db.Column(db.Text)
    
    # Guarantor Information
    guarantor_name = db.Column(db.String(100))
    guarantor_phone = db.Column(db.String(20))
    guarantor_address = db.Column(db.Text)
    guarantor_relationship = db.Column(db.String(50))
    
    # Application Status
    application_status = db.Column(db.Enum(VerificationStatus), default=VerificationStatus.PENDING)
    application_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    approval_date = db.Column(db.DateTime)
    
    # Officer Assignment
    assigned_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'loan_purpose': self.loan_purpose.value if self.loan_purpose else None,
            'loan_amount': float(self.loan_amount) if self.loan_amount else None,
            'loan_term': self.loan_term,
            'interest_rate': float(self.interest_rate) if self.interest_rate else None,
            'has_collateral': self.has_collateral,
            'collateral_type': self.collateral_type,
            'collateral_value': float(self.collateral_value) if self.collateral_value else None,
            'collateral_description': self.collateral_description,
            'guarantor_name': self.guarantor_name,
            'guarantor_phone': self.guarantor_phone,
            'guarantor_address': self.guarantor_address,
            'guarantor_relationship': self.guarantor_relationship,
            'application_status': self.application_status.value if self.application_status else None,
            'application_date': self.application_date.isoformat() if self.application_date else None,
            'approval_date': self.approval_date.isoformat() if self.approval_date else None,
            'assigned_officer_id': self.assigned_officer_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# API Endpoints

@profile_bp.route('/borrower/<int:borrower_id>', methods=['GET'])
@login_required
def get_borrower_profile(borrower_id):
    """Get borrower profile"""
    try:
        profile = BorrowerProfile.query.filter_by(borrower_id=borrower_id).first()
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        return jsonify({'profile': profile.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/borrower/<int:borrower_id>', methods=['POST', 'PUT'])
@login_required
def create_or_update_profile(borrower_id):
    """Create or update borrower profile"""
    try:
        data = request.get_json()
        
        # Get or create profile
        profile = BorrowerProfile.query.filter_by(borrower_id=borrower_id).first()
        if not profile:
            profile = BorrowerProfile(borrower_id=borrower_id)
            db.session.add(profile)
        
        # Update profile fields
        updateable_fields = [
            'full_name', 'date_of_birth', 'phone_number', 'email', 'address',
            'city', 'state', 'country', 'marital_status', 'bvn', 'nin',
            'primary_id_type', 'primary_id_number', 'employment_type',
            'employer_name', 'job_title', 'work_address', 'monthly_income',
            'employment_start_date', 'business_name', 'business_registration_number',
            'business_address', 'business_type', 'annual_revenue',
            'bank_name', 'account_number', 'account_name', 'account_type'
        ]
        
        for field in updateable_fields:
            if field in data:
                value = data[field]
                if field == 'date_of_birth' and value:
                    value = datetime.strptime(value, '%Y-%m-%d').date()
                elif field == 'employment_start_date' and value:
                    value = datetime.strptime(value, '%Y-%m-%d').date()
                elif field in ['marital_status', 'primary_id_type', 'employment_type']:
                    if value:
                        enum_class = {
                            'marital_status': MaritalStatus,
                            'primary_id_type': IdentificationType,
                            'employment_type': EmploymentType
                        }[field]
                        value = enum_class(value)
                
                setattr(profile, field, value)
        
        profile.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'profile': profile.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/borrower/<int:borrower_id>/documents', methods=['POST'])
@login_required
def upload_document(borrower_id):
    """Upload document for borrower"""
    try:
        data = request.get_json()
        
        # Get profile
        profile = BorrowerProfile.query.filter_by(borrower_id=borrower_id).first()
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Create document record
        document = ProfileDocument(
            profile_id=profile.id,
            document_type=data.get('document_type'),
            document_name=data.get('document_name'),
            document_data=data.get('document_data'),  # Base64 encoded data from browser
            document_path=data.get('document_path')   # File path if uploaded
        )
        
        db.session.add(document)
        db.session.commit()
        
        return jsonify({
            'message': 'Document uploaded successfully',
            'document': document.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/borrower/<int:borrower_id>/loan-application', methods=['POST'])
@login_required
def create_loan_application(borrower_id):
    """Create loan application"""
    try:
        data = request.get_json()
        
        # Get profile
        profile = BorrowerProfile.query.filter_by(borrower_id=borrower_id).first()
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Create loan application
        application = LoanApplication(
            profile_id=profile.id,
            loan_purpose=LoanPurpose(data.get('loan_purpose')),
            loan_amount=data.get('loan_amount'),
            loan_term=data.get('loan_term'),
            interest_rate=data.get('interest_rate'),
            has_collateral=data.get('has_collateral', False),
            collateral_type=data.get('collateral_type'),
            collateral_value=data.get('collateral_value'),
            collateral_description=data.get('collateral_description'),
            guarantor_name=data.get('guarantor_name'),
            guarantor_phone=data.get('guarantor_phone'),
            guarantor_address=data.get('guarantor_address'),
            guarantor_relationship=data.get('guarantor_relationship'),
            assigned_officer_id=current_user.id
        )
        
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'message': 'Loan application created successfully',
            'application': application.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/loan-applications', methods=['GET'])
@login_required
def get_loan_applications():
    """Get all loan applications"""
    try:
        if current_user.is_admin():
            applications = LoanApplication.query.all()
        else:
            applications = LoanApplication.query.filter_by(assigned_officer_id=current_user.id).all()
        
        return jsonify({
            'applications': [app.to_dict() for app in applications]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/verification/bvn', methods=['POST'])
@login_required
def verify_bvn():
    """Mock BVN verification endpoint"""
    try:
        data = request.get_json()
        bvn = data.get('bvn')
        
        # Mock verification logic
        if bvn and len(bvn) == 11 and bvn.isdigit():
            return jsonify({
                'verified': True,
                'message': 'BVN verified successfully',
                'data': {
                    'name': 'John Doe',
                    'date_of_birth': '1990-01-01',
                    'phone': '08012345678'
                }
            }), 200
        else:
            return jsonify({
                'verified': False,
                'message': 'Invalid BVN format'
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/verification/nin', methods=['POST'])
@login_required  
def verify_nin():
    """Mock NIN verification endpoint"""
    try:
        data = request.get_json()
        nin = data.get('nin')
        
        # Mock verification logic
        if nin and len(nin) == 11 and nin.isdigit():
            return jsonify({
                'verified': True,
                'message': 'NIN verified successfully',
                'data': {
                    'name': 'John Doe',
                    'date_of_birth': '1990-01-01',
                    'address': '123 Main Street, Lagos'
                }
            }), 200
        else:
            return jsonify({
                'verified': False,
                'message': 'Invalid NIN format'
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/enums', methods=['GET'])
@login_required
def get_enums():
    """Get all enum values for frontend"""
    try:
        return jsonify({
            'marital_status': [status.value for status in MaritalStatus],
            'employment_type': [emp_type.value for emp_type in EmploymentType],
            'identification_type': [id_type.value for id_type in IdentificationType],
            'loan_purpose': [purpose.value for purpose in LoanPurpose],
            'verification_status': [status.value for status in VerificationStatus]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
