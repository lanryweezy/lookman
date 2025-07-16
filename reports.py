from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from user import db, User
from loans import Loan
from payments import Payment
from sqlalchemy import func
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/daily-collections', methods=['GET'])
@login_required
def daily_collections_report():
    """
    Report for daily collections, with breakdowns by officer.
    """
    try:
        report_date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
        
        # Query for payments on the given date
        payments_query = db.session.query(
            Payment.recorded_by,
            func.sum(Payment.expected_amount).label('total_expected'),
            func.sum(Payment.actual_amount).label('total_collected'),
            func.count(Payment.id).label('payment_count')
        ).filter(Payment.payment_date == report_date).group_by(Payment.recorded_by)
        
        # Filter by user role if not admin
        if not current_user.is_admin():
            payments_query = payments_query.join(Loan).filter(Loan.account_officer_id == current_user.id)
        
        payments_data = payments_query.all()
        
        # Get user details for officer names
        officer_ids = [p.recorded_by for p in payments_data]
        officers = User.query.filter(User.id.in_(officer_ids)).all()
        officer_map = {o.id: o.full_name for o in officers}
        
        # Build officer breakdown
        officer_breakdown = []
        total_expected = 0
        total_collected = 0
        total_payments = 0

        for payment in payments_data:
            expected = payment.total_expected or 0
            collected = payment.total_collected or 0
            
            officer_breakdown.append({
                'officer_id': payment.recorded_by,
                'officer_name': officer_map.get(payment.recorded_by, 'Unknown'),
                'expected': float(expected),
                'collected': float(collected),
                'collection_rate': (float(collected / expected) * 100) if expected > 0 else 0,
                'payment_count': payment.payment_count
            })
            
            total_expected += expected
            total_collected += collected
            total_payments += payment.payment_count

        # Overall summary
        summary = {
            'report_date': report_date.isoformat(),
            'total_expected': float(total_expected),
            'total_collected': float(total_collected),
            'collection_rate': (float(total_collected / total_expected) * 100) if total_expected > 0 else 0,
            'payment_count': total_payments
        }
        
        return jsonify({
            'report': {
                'title': 'Daily Collections Report',
                'summary': summary,
                'officer_breakdown': officer_breakdown
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/outstanding-loans', methods=['GET'])
@login_required
def outstanding_loans_report():
    """
    Report for all outstanding and overdue loans.
    """
    try:
        query = Loan.query.filter(Loan.status.in_(['active', 'overdue']))
        
        # Filter by user role if not admin
        if not current_user.is_admin():
            query = query.filter(Loan.account_officer_id == current_user.id)
        
        loans = query.all()
        
        # Calculate summary
        total_outstanding = sum(loan.get_outstanding_balance() for loan in loans)
        overdue_loans = [loan for loan in loans if loan.is_overdue()]
        overdue_outstanding = sum(loan.get_outstanding_balance() for loan in overdue_loans)

        summary = {
            'total_loans': len(loans),
            'total_outstanding': float(total_outstanding),
            'overdue_loans_count': len(overdue_loans),
            'overdue_outstanding': float(overdue_outstanding),
            'overdue_percentage': (float(len(overdue_loans) / len(loans)) * 100) if loans else 0
        }
        
        # Prepare loan details
        loan_details = []
        for loan in loans:
            loan_details.append({
                'id': loan.id,
                'borrower_name': loan.borrower.name,
                'principal_amount': float(loan.principal_amount),
                'outstanding_balance': float(loan.get_outstanding_balance()),
                'status': loan.status,
                'days_overdue': (date.today() - loan.expected_end_date).days if loan.is_overdue() else 0
            })

        return jsonify({
            'report': {
                'title': 'Outstanding Loans Report',
                'summary': summary,
                'loans': loan_details
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/profit-loss', methods=['GET'])
@login_required
def profit_loss_report():
    """
    Report for profit and loss analysis.
    """
    try:
        # Get date range from query params
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'Start date and end date are required'}), 400
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Revenue calculation
        loans_in_period = Loan.query.filter(Loan.start_date.between(start_date, end_date)).all()
        
        principal_disbursed = sum(loan.principal_amount for loan in loans_in_period)
        interest_income = sum(loan.interest_amount for loan in loans_in_period)
        fee_income = sum(loan.expenses for loan in loans_in_period)
        gross_revenue = interest_income + fee_income
        
        revenue = {
            'principal_disbursed': float(principal_disbursed),
            'interest_income': float(interest_income),
            'fee_income': float(fee_income),
            'gross_revenue': float(gross_revenue)
        }
        
        # Expenses calculation (mock for now)
        salary_expenses = 0 # Placeholder for salary expenses
        total_expenses = salary_expenses
        
        expenses = {
            'salary_expenses': float(salary_expenses),
            'total_expenses': float(total_expenses)
        }
        
        # Profit calculation
        net_profit = gross_revenue - total_expenses
        profit_margin = (net_profit / gross_revenue * 100) if gross_revenue > 0 else 0
        
        profit = {
            'gross_profit': float(gross_revenue),
            'net_profit': float(net_profit),
            'profit_margin': profit_margin
        }
        
        return jsonify({
            'report': {
                'title': 'Profit & Loss Report',
                'period': f'{start_date.isoformat()} to {end_date.isoformat()}',
                'revenue': revenue,
                'expenses': expenses,
                'profit': profit
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/performance', methods=['GET'])
@login_required
def performance_report():
    """
    Report for staff performance metrics.
    """
    try:
        # Get user filter from query params
        user_id = request.args.get('user_id')
        
        # Base query for users
        query = User.query.filter_by(role='account_officer')
        if user_id:
            query = query.filter_by(id=user_id)
        
        users = query.all()
        
        performance_data = []
        
        for user in users:
            # Loan metrics
            loans = Loan.query.filter_by(account_officer_id=user.id).all()
            total_loans = len(loans)
            active_loans = len([l for l in loans if l.status == 'active'])
            completed_loans = len([l for l in loans if l.status == 'completed'])
            completion_rate = (completed_loans / total_loans * 100) if total_loans > 0 else 0
            
            # Collection metrics
            payments = Payment.query.join(Loan).filter(Loan.account_officer_id == user.id).all()
            total_expected = sum(p.expected_amount for p in payments)
            total_collected = sum(p.actual_amount for p in payments)
            collection_rate = (total_collected / total_expected * 100) if total_expected > 0 else 0
            
            # Portfolio metrics
            total_portfolio = sum(l.principal_amount for l in loans)
            outstanding_portfolio = sum(l.get_outstanding_balance() for l in loans if l.status == 'active')
            
            performance_data.append({
                'user': user.to_dict(),
                'loan_metrics': {
                    'total_loans': total_loans,
                    'active_loans': active_loans,
                    'completed_loans': completed_loans,
                    'completion_rate': completion_rate
                },
                'collection_metrics': {
                    'total_payments': len(payments),
                    'total_expected': float(total_expected),
                    'total_collected': float(total_collected),
                    'collection_rate': collection_rate
                },
                'portfolio_metrics': {
                    'total_portfolio': float(total_portfolio),
                    'outstanding_portfolio': float(outstanding_portfolio)
                }
            })

        return jsonify({
            'report': {
                'title': 'Staff Performance Report',
                'performance_data': performance_data
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
