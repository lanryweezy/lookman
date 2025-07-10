from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from user import db, User
from salary import SalaryCalculation
from auth import admin_required, account_officer_required
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_

# Import models after their definitions (circular import workaround)
def get_models():
    from loans import Loan
    from payments import Payment
    from borrowers import Borrower
    return Loan, Payment, Borrower

# Use this pattern in functions instead of direct imports

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/daily-collections', methods=['GET'])
@login_required
@account_officer_required
def daily_collections_report():
    """Generate daily collections report"""
    try:
        # Get query parameters
        report_date_str = request.args.get('date', date.today().isoformat())
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
        
        # Get model classes
        Loan, Payment, Borrower = get_models()
        
        # Base query for payments on the specified date
        query = Payment.query.join(Loan).filter(Payment.payment_date == report_date)
        
        # Filter by user role
        if not current_user.is_admin():
            query = query.filter(Loan.account_officer_id == current_user.id)
        
        payments = query.all()
        
        # Calculate summary statistics
        total_expected = sum(payment.expected_amount for payment in payments)
        total_collected = sum(payment.actual_amount for payment in payments)
        collection_rate = float(total_collected / total_expected * 100) if total_expected > 0 else 0
        
        # Group by account officer
        officer_summary = {}
        for payment in payments:
            officer_id = payment.loan.account_officer_id
            officer_name = payment.loan.account_officer.full_name
            
            if officer_id not in officer_summary:
                officer_summary[officer_id] = {
                    'officer_name': officer_name,
                    'expected': Decimal('0.00'),
                    'collected': Decimal('0.00'),
                    'payment_count': 0
                }
            
            officer_summary[officer_id]['expected'] += payment.expected_amount
            officer_summary[officer_id]['collected'] += payment.actual_amount
            officer_summary[officer_id]['payment_count'] += 1
        
        # Convert to list and add collection rates
        officer_list = []
        for officer_data in officer_summary.values():
            officer_data['collection_rate'] = float(
                officer_data['collected'] / officer_data['expected'] * 100
            ) if officer_data['expected'] > 0 else 0
            officer_data['expected'] = float(officer_data['expected'])
            officer_data['collected'] = float(officer_data['collected'])
            officer_list.append(officer_data)
        
        report = {
            'date': report_date.isoformat(),
            'summary': {
                'total_expected': float(total_expected),
                'total_collected': float(total_collected),
                'collection_rate': collection_rate,
                'payment_count': len(payments)
            },
            'officer_breakdown': officer_list,
            'payments': [payment.to_dict() for payment in payments]
        }
        
        return jsonify({'report': report}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/outstanding-loans', methods=['GET'])
@login_required
@account_officer_required
def outstanding_loans_report():
    """Generate outstanding loans report"""
    try:
        # Get model classes
        Loan, Payment, Borrower = get_models()
        
        # Base query for active loans
        query = Loan.query.filter(Loan.status.in_(['active', 'overdue']))
        
        # Filter by user role
        if not current_user.is_admin():
            query = query.filter_by(account_officer_id=current_user.id)
        
        loans = query.all()
        
        # Calculate outstanding amounts and categorize
        total_outstanding = Decimal('0.00')
        overdue_outstanding = Decimal('0.00')
        current_outstanding = Decimal('0.00')
        
        loan_details = []
        for loan in loans:
            outstanding = loan.get_outstanding_balance()
            total_outstanding += outstanding
            
            if loan.status == 'overdue':
                overdue_outstanding += outstanding
            else:
                current_outstanding += outstanding
            
            # Calculate days overdue
            days_overdue = 0
            if loan.is_overdue():
                days_overdue = (date.today() - loan.expected_end_date).days
            
            loan_details.append({
                **loan.to_dict(),
                'outstanding_balance': float(outstanding),
                'days_overdue': days_overdue
            })
        
        # Sort by outstanding balance (highest first)
        loan_details.sort(key=lambda x: x['outstanding_balance'], reverse=True)
        
        report = {
            'generated_date': date.today().isoformat(),
            'summary': {
                'total_loans': len(loans),
                'total_outstanding': float(total_outstanding),
                'current_outstanding': float(current_outstanding),
                'overdue_outstanding': float(overdue_outstanding),
                'overdue_percentage': float(overdue_outstanding / total_outstanding * 100) if total_outstanding > 0 else 0
            },
            'loans': loan_details
        }
        
        return jsonify({'report': report}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/profit-loss', methods=['GET'])
@login_required
@admin_required
def profit_loss_report():
    """Generate profit and loss report"""
    try:
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Default to current month if no dates provided
        if not start_date_str or not end_date_str:
            today = date.today()
            start_date = date(today.year, today.month, 1)
            if today.month == 12:
                end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Get model classes
        Loan, Payment, Borrower = get_models()
        
        # Get loans created in the period
        loans_in_period = Loan.query.filter(
            Loan.start_date >= start_date,
            Loan.start_date <= end_date
        ).all()
        
        # Calculate revenue components
        total_principal = sum(loan.principal_amount for loan in loans_in_period)
        total_interest = sum(loan.interest_amount for loan in loans_in_period)
        total_fees = sum(loan.expenses for loan in loans_in_period)
        gross_revenue = total_interest + total_fees
        
        # Calculate collections in the period (regardless of loan start date)
        total_collections = db.session.query(func.sum(Payment.actual_amount)).filter(
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date
        ).scalar() or Decimal('0.00')
        
        # Calculate salary expenses for the period
        period_str = f"{start_date.year}-{start_date.month:02d}"
        salary_expenses = db.session.query(func.sum(SalaryCalculation.total_salary)).filter(
            SalaryCalculation.calculation_period == period_str
        ).scalar() or Decimal('0.00')
        
        # Calculate net profit
        net_profit = gross_revenue - salary_expenses
        
        # Calculate key ratios
        profit_margin = float(net_profit / gross_revenue * 100) if gross_revenue > 0 else 0
        collection_efficiency = float(total_collections / total_principal * 100) if total_principal > 0 else 0
        
        report = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'revenue': {
                'principal_disbursed': float(total_principal),
                'interest_income': float(total_interest),
                'fee_income': float(total_fees),
                'gross_revenue': float(gross_revenue)
            },
            'expenses': {
                'salary_expenses': float(salary_expenses),
                'total_expenses': float(salary_expenses)
            },
            'profit': {
                'gross_profit': float(gross_revenue),
                'net_profit': float(net_profit),
                'profit_margin': profit_margin
            },
            'cash_flow': {
                'collections_received': float(total_collections),
                'collection_efficiency': collection_efficiency
            },
            'loan_metrics': {
                'loans_disbursed': len(loans_in_period),
                'average_loan_size': float(total_principal / len(loans_in_period)) if loans_in_period else 0
            }
        }
        
        return jsonify({'report': report}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/performance', methods=['GET'])
@login_required
@account_officer_required
def performance_report():
    """Generate performance report for account officers"""
    try:
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        user_id = request.args.get('user_id')
        
        # Default to current month if no dates provided
        if not start_date_str or not end_date_str:
            today = date.today()
            start_date = date(today.year, today.month, 1)
            if today.month == 12:
                end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Get model classes
        Loan, Payment, Borrower = get_models()
        
        # Determine which users to include
        if current_user.is_admin():
            if user_id:
                users = [User.query.get_or_404(user_id)]
            else:
                users = User.query.filter_by(role='account_officer', is_active=True).all()
        else:
            users = [current_user]
        
        performance_data = []
        
        for user in users:
            # Get loans managed by this user
            user_loans = Loan.query.filter_by(account_officer_id=user.id).all()
            
            # Calculate loan metrics
            total_loans = len(user_loans)
            active_loans = len([loan for loan in user_loans if loan.status == 'active'])
            completed_loans = len([loan for loan in user_loans if loan.status == 'completed'])
            overdue_loans = len([loan for loan in user_loans if loan.status == 'overdue'])
            
            # Calculate collections for the period
            period_collections = db.session.query(func.sum(Payment.actual_amount)).join(Loan).filter(
                Loan.account_officer_id == user.id,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date
            ).scalar() or Decimal('0.00')
            
            # Calculate expected collections for the period
            period_expected = db.session.query(func.sum(Payment.expected_amount)).join(Loan).filter(
                Loan.account_officer_id == user.id,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date
            ).scalar() or Decimal('0.00')
            
            # Calculate collection rate
            collection_rate = float(period_collections / period_expected * 100) if period_expected > 0 else 0
            
            # Calculate total portfolio value
            total_portfolio = sum(loan.principal_amount for loan in user_loans)
            outstanding_portfolio = sum(loan.get_outstanding_balance() for loan in user_loans if loan.status in ['active', 'overdue'])
            
            performance_data.append({
                'user': user.to_dict(),
                'loan_metrics': {
                    'total_loans': total_loans,
                    'active_loans': active_loans,
                    'completed_loans': completed_loans,
                    'overdue_loans': overdue_loans,
                    'completion_rate': float(completed_loans / total_loans * 100) if total_loans > 0 else 0,
                    'overdue_rate': float(overdue_loans / total_loans * 100) if total_loans > 0 else 0
                },
                'collection_metrics': {
                    'period_collections': float(period_collections),
                    'period_expected': float(period_expected),
                    'collection_rate': collection_rate
                },
                'portfolio_metrics': {
                    'total_portfolio': float(total_portfolio),
                    'outstanding_portfolio': float(outstanding_portfolio),
                    'average_loan_size': float(total_portfolio / total_loans) if total_loans > 0 else 0
                }
            })
        
        # Sort by collection rate (highest first)
        performance_data.sort(key=lambda x: x['collection_metrics']['collection_rate'], reverse=True)
        
        report = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'performance_data': performance_data
        }
        
        return jsonify({'report': report}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/monthly-summary', methods=['GET'])
@login_required
@admin_required
def monthly_summary_report():
    """Generate comprehensive monthly summary report"""
    try:
        # Get query parameters
        year = int(request.args.get('year', date.today().year))
        month = int(request.args.get('month', date.today().month))
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get model classes
        Loan, Payment, Borrower = get_models()
        
        # Loan statistics
        loans_created = Loan.query.filter(
            Loan.start_date >= start_date,
            Loan.start_date <= end_date
        ).count()
        
        loans_completed = Loan.query.filter(
            Loan.actual_end_date >= start_date,
            Loan.actual_end_date <= end_date
        ).count()
        
        # Financial statistics
        total_disbursed = db.session.query(func.sum(Loan.principal_amount)).filter(
            Loan.start_date >= start_date,
            Loan.start_date <= end_date
        ).scalar() or Decimal('0.00')
        
        total_collections = db.session.query(func.sum(Payment.actual_amount)).filter(
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date
        ).scalar() or Decimal('0.00')
        
        # Outstanding loans at end of month
        outstanding_loans = Loan.query.filter(
            Loan.status.in_(['active', 'overdue']),
            Loan.start_date <= end_date
        ).count()
        
        total_outstanding = sum(
            loan.get_outstanding_balance() 
            for loan in Loan.query.filter(
                Loan.status.in_(['active', 'overdue']),
                Loan.start_date <= end_date
            ).all()
        )
        
        # Salary costs
        period_str = f"{year}-{month:02d}"
        salary_costs = db.session.query(func.sum(SalaryCalculation.total_salary)).filter(
            SalaryCalculation.calculation_period == period_str
        ).scalar() or Decimal('0.00')
        
        report = {
            'period': {
                'year': year,
                'month': month,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'loan_activity': {
                'loans_created': loans_created,
                'loans_completed': loans_completed,
                'total_disbursed': float(total_disbursed),
                'average_loan_size': float(total_disbursed / loans_created) if loans_created > 0 else 0
            },
            'collections': {
                'total_collections': float(total_collections),
                'daily_average': float(total_collections / (end_date - start_date).days)
            },
            'portfolio': {
                'outstanding_loans': outstanding_loans,
                'total_outstanding': float(total_outstanding),
                'average_outstanding': float(total_outstanding / outstanding_loans) if outstanding_loans > 0 else 0
            },
            'expenses': {
                'salary_costs': float(salary_costs)
            },
            'profitability': {
                'net_cash_flow': float(total_collections - total_disbursed),
                'expense_ratio': float(salary_costs / total_collections * 100) if total_collections > 0 else 0
            }
        }
        
        return jsonify({'report': report}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

