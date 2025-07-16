from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from user import db, User
from auth import admin_required
from datetime import datetime
import re

profile_bp = Blueprint('profile', __name__)

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"

    # Check for at least one letter and one number
    if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        return False, "Password must contain at least one letter and one number"

    return True, "Password is valid"

def validate_email(email):
    """Validate email format"""
    if not email:
        return True  # Email is optional

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, email):
        return True
    return False

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True  # Phone is optional

    # Remove any non-digit characters for validation
    digits_only = re.sub(r'\D', '', phone)

    # Check if it's a valid Nigerian phone number (11 digits starting with 0 or 10 digits)
    if len(digits_only) in [10, 11]:
        return True

    return False

@profile_bp.route('/dashboard')
@login_required
def profile_dashboard():
    """Main profile management dashboard"""
    return render_template('user_profile.html')

@profile_bp.route('/current', methods=['GET'])
@login_required
def get_current_user_profile():
    """Get current user's profile information"""
    try:
        return jsonify({
            'success': True,
            'user': current_user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@profile_bp.route('/update', methods=['POST', 'PUT'])
@login_required
def update_profile():
    """Update current user's profile information"""
    try:
        data = request.get_json()

        # Validate required fields
        if 'full_name' not in data or not data['full_name'].strip():
            return jsonify({
                'success': False,
                'error': 'Full name is required'
            }), 400

        # Validate email if provided
        if 'email' in data and data['email']:
            if not validate_email(data['email']):
                return jsonify({
                    'success': False,
                    'error': 'Invalid email format'
                }), 400

        # Validate phone if provided
        if 'phone' in data and data['phone']:
            if not validate_phone(data['phone']):
                return jsonify({
                    'success': False,
                    'error': 'Invalid phone number format'
                }), 400

        # Update user profile
        current_user.full_name = data['full_name'].strip()
        current_user.email = data.get('email', '').strip() or None
        current_user.phone = data.get('phone', '').strip() or None
        current_user.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@profile_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change current user's password"""
    try:
        data = request.get_json()

        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        # Validate input
        if not current_password or not new_password or not confirm_password:
            return jsonify({
                'success': False,
                'error': 'All password fields are required'
            }), 400

        # Check if new passwords match
        if new_password != confirm_password:
            return jsonify({
                'success': False,
                'error': 'New passwords do not match'
            }), 400

        # Validate current password (skip for first login)
        if not current_user.is_first_login:
            if not current_user.check_password(current_password):
                return jsonify({
                    'success': False,
                    'error': 'Current password is incorrect'
                }), 400

        # Validate new password strength
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': message
            }), 400

        # Set new password
        current_user.set_password(new_password)
        current_user.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@profile_bp.route('/admin/users', methods=['GET'])
@login_required
@admin_required
def get_all_users():
    """Get all users for admin management"""
    try:
        users = User.query.all()
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users],
            'total': len(users)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@profile_bp.route('/admin/user/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user_by_id(user_id):
    """Get specific user by ID (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@profile_bp.route('/admin/user/<int:user_id>/update', methods=['POST', 'PUT'])
@login_required
@admin_required
def admin_update_user(user_id):
    """Update user profile (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()

        # Validate required fields
        if 'full_name' not in data or not data['full_name'].strip():
            return jsonify({
                'success': False,
                'error': 'Full name is required'
            }), 400

        # Validate email if provided
        if 'email' in data and data['email']:
            if not validate_email(data['email']):
                return jsonify({
                    'success': False,
                    'error': 'Invalid email format'
                }), 400

        # Validate phone if provided
        if 'phone' in data and data['phone']:
            if not validate_phone(data['phone']):
                return jsonify({
                    'success': False,
                    'error': 'Invalid phone number format'
                }), 400

        # Update user profile
        user.full_name = data['full_name'].strip()
        user.email = data.get('email', '').strip() or None
        user.phone = data.get('phone', '').strip() or None

        # Admin can update role and active status
        if 'role' in data and data['role'] in ['admin', 'account_officer']:
            user.role = data['role']

        if 'is_active' in data:
            user.is_active = bool(data['is_active'])

        user.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'User profile updated successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@profile_bp.route('/admin/user/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    """Reset user password (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()

        new_password = data.get('new_password')
        force_change = data.get('force_change', True)

        if not new_password:
            return jsonify({
                'success': False,
                'error': 'New password is required'
            }), 400

        # Validate new password strength
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': message
            }), 400

        # Set new password
        user.set_password(new_password)

        # Force user to change password on next login if requested
        if force_change:
            user.is_first_login = True

        user.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Password reset successfully',
            'force_change': force_change
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@profile_bp.route('/admin/user/create', methods=['POST'])
@login_required
@admin_required
def admin_create_user():
    """Create new user (admin only)"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['username', 'full_name', 'password', 'role']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'error': f'{field.replace("_", " ").title()} is required'
                }), 400

        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({
                'success': False,
                'error': 'Username already exists'
            }), 400

        # Validate email if provided
        if 'email' in data and data['email']:
            if not validate_email(data['email']):
                return jsonify({
                    'success': False,
                    'error': 'Invalid email format'
                }), 400

        # Validate phone if provided
        if 'phone' in data and data['phone']:
            if not validate_phone(data['phone']):
                return jsonify({
                    'success': False,
                    'error': 'Invalid phone number format'
                }), 400

        # Validate role
        if data['role'] not in ['admin', 'account_officer']:
            return jsonify({
                'success': False,
                'error': 'Invalid role specified'
            }), 400

        # Validate password strength
        is_valid, message = validate_password_strength(data['password'])
        if not is_valid:
            return jsonify({
                'success': False,
                'error': message
            }), 400

        # Create new user
        new_user = User(
            username=data['username'].strip(),
            full_name=data['full_name'].strip(),
            email=data.get('email', '').strip() or None,
            phone=data.get('phone', '').strip() or None,
            role=data['role'],
            is_active=data.get('is_active', True),
            is_first_login=True  # Force password change on first login
        )

        new_user.set_password(data['password'])

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@profile_bp.route('/admin/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status (admin only)"""
    try:
        user = User.query.get_or_404(user_id)

        # Prevent admin from deactivating themselves
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'error': 'You cannot deactivate your own account'
            }), 400

        user.is_active = not user.is_active
        user.updated_at = datetime.utcnow()

        db.session.commit()

        status = 'activated' if user.is_active else 'deactivated'

        return jsonify({
            'success': True,
            'message': f'User {status} successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@profile_bp.route('/check-first-login', methods=['GET'])
@login_required
def check_first_login():
    """Check if current user needs to change password"""
    try:
        return jsonify({
            'success': True,
            'is_first_login': current_user.is_first_login,
            'last_password_change': current_user.last_password_change.isoformat() if current_user.last_password_change else None
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@profile_bp.route('/profile-stats', methods=['GET'])
@login_required
def get_profile_stats():
    """Get profile completion and security stats"""
    try:
        # Calculate profile completion
        completion_score = 0
        total_fields = 4  # username, full_name, email, phone

        if current_user.username:
            completion_score += 1
        if current_user.full_name:
            completion_score += 1
        if current_user.email:
            completion_score += 1
        if current_user.phone:
            completion_score += 1

        completion_percentage = (completion_score / total_fields) * 100

        # Calculate password age in days
        password_age = None
        if current_user.last_password_change:
            password_age = (datetime.utcnow() - current_user.last_password_change).days

        return jsonify({
            'success': True,
            'stats': {
                'profile_completion': completion_percentage,
                'password_age_days': password_age,
                'is_first_login': current_user.is_first_login,
                'account_age_days': (datetime.utcnow() - current_user.created_at).days,
                'last_updated': current_user.updated_at.isoformat() if current_user.updated_at else None
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
