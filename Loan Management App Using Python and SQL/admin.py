from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from user import db, User
from auth import admin_required
from datetime import datetime, timedelta
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Get all users"""
    try:
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        full_name = data.get('full_name')
        role = data.get('role', 'account_officer')
        
        # Validation
        if not username or not password or not full_name:
            return jsonify({'error': 'Username, password, and full name are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        if role not in ['admin', 'account_officer']:
            return jsonify({'error': 'Invalid role'}), 400
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 400
        
        # Create new user
        new_user = User(
            username=username,
            full_name=full_name,
            role=role
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """Update a user"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'full_name' in data:
            user.full_name = data['full_name']
        
        if 'role' in data:
            if data['role'] not in ['admin', 'account_officer']:
                return jsonify({'error': 'Invalid role'}), 400
            user.role = data['role']
        
        if 'is_active' in data:
            user.is_active = bool(data['is_active'])
        
        if 'password' in data:
            if len(data['password']) < 6:
                return jsonify({'error': 'Password must be at least 6 characters long'}), 400
            user.set_password(data['password'])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent deleting the current admin user
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        # Check if user has associated data
        from loans import Loan
        loan_count = Loan.query.filter_by(account_officer_id=user_id).count()
        if loan_count > 0:
            return jsonify({'error': f'Cannot delete user with {loan_count} associated loans'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/dashboard/stats', methods=['GET'])
@login_required
@admin_required
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Import models to avoid circular imports
        from borrowers import Borrower
        from loans import Loan
        from payments import Payment
        
        # Get basic counts
        total_users = User.query.count()
        total_borrowers = Borrower.query.count()
        total_loans = Loan.query.count()
        active_loans = Loan.query.filter_by(status='active').count()
        completed_loans = Loan.query.filter_by(status='completed').count()
        overdue_loans = Loan.query.filter_by(status='overdue').count()
        
        # Get financial stats
        total_principal = db.session.query(func.sum(Loan.principal_amount)).scalar() or 0
        total_collections = db.session.query(func.sum(Payment.actual_amount)).scalar() or 0
        
        # Get today's collections
        today = datetime.now().date()
        today_collections = db.session.query(func.sum(Payment.actual_amount)).filter(
            Payment.payment_date == today
        ).scalar() or 0
        
        # Get this month's collections
        first_day_of_month = today.replace(day=1)
        month_collections = db.session.query(func.sum(Payment.actual_amount)).filter(
            Payment.payment_date >= first_day_of_month
        ).scalar() or 0
        
        return jsonify({
            'stats': {
                'total_users': total_users,
                'total_borrowers': total_borrowers,
                'total_loans': total_loans,
                'active_loans': active_loans,
                'completed_loans': completed_loans,
                'overdue_loans': overdue_loans,
                'total_principal': float(total_principal),
                'total_collections': float(total_collections),
                'today_collections': float(today_collections),
                'month_collections': float(month_collections)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/settings', methods=['GET'])
@login_required
@admin_required
def get_settings():
    """Get all system settings"""
    try:
        from settings import SystemSetting
        settings = SystemSetting.query.all()
        return jsonify({
            'settings': [setting.to_dict() for setting in settings]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/settings', methods=['POST'])
@login_required
@admin_required
def update_settings():
    """Update system settings"""
    try:
        data = request.get_json()
        settings_data = data.get('settings', [])
        
        for setting_data in settings_data:
            key = setting_data.get('setting_key')
            value = setting_data.get('setting_value')
            description = setting_data.get('description')
            
            if key and value is not None:
                SystemSetting.set_setting(key, value, description, current_user.id)
        
        return jsonify({'message': 'Settings updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

