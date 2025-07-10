"""
Automation utilities for Lookman loan management system
"""

from flask import Blueprint
from user import db, User
from salary import SalaryCalculation
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func
import logging

automation_bp = Blueprint('automation', __name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentAutomation:
    """Handles automated payment tracking and loan status updates"""
    
    @staticmethod
    def update_all_loan_statuses():
        """Update status for all active loans based on payments and dates"""
        try:
            active_loans = Loan.query.filter_by(status='active').all()
            updated_count = 0
            
            for loan in active_loans:
                old_status = loan.status
                loan.update_status()
                
                if loan.status != old_status:
                    updated_count += 1
                    logger.info(f"Loan {loan.id} status changed from {old_status} to {loan.status}")
            
            db.session.commit()
            logger.info(f"Updated status for {updated_count} loans")
            return updated_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating loan statuses: {str(e)}")
            return 0
    
    @staticmethod
    def identify_overdue_loans():
        """Identify and mark overdue loans"""
        try:
            today = date.today()
            overdue_loans = Loan.query.filter(
                Loan.status == 'active',
                Loan.expected_end_date < today
            ).all()
            
            updated_count = 0
            for loan in overdue_loans:
                loan.status = 'overdue'
                updated_count += 1
                logger.info(f"Marked loan {loan.id} as overdue")
            
            db.session.commit()
            logger.info(f"Marked {updated_count} loans as overdue")
            return overdue_loans
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error identifying overdue loans: {str(e)}")
            return []
    
    @staticmethod
    def get_expected_payments_today():
        """Get all expected payments for today"""
        try:
            today = date.today()
            active_loans = Loan.query.filter_by(status='active').all()
            expected_payments = []
            
            for loan in active_loans:
                schedule = loan.get_payment_schedule()
                
                for day_info in schedule:
                    if day_info['date'] == today:
                        # Check if payment already exists
                        existing_payment = Payment.query.filter_by(
                            loan_id=loan.id,
                            payment_day=day_info['day']
                        ).first()
                        
                        if not existing_payment:
                            expected_payments.append({
                                'loan_id': loan.id,
                                'borrower_name': loan.borrower.name,
                                'payment_day': day_info['day'],
                                'expected_amount': float(loan.daily_repayment),
                                'account_officer': loan.account_officer.full_name
                            })
            
            return expected_payments
            
        except Exception as e:
            logger.error(f"Error getting expected payments: {str(e)}")
            return []
    
    @staticmethod
    def auto_create_payment_records():
        """Automatically create payment records for today's expected payments"""
        try:
            expected_payments = PaymentAutomation.get_expected_payments_today()
            created_count = 0
            
            for payment_info in expected_payments:
                # Create payment record with 0 actual amount (to be updated when payment is made)
                new_payment = Payment(
                    loan_id=payment_info['loan_id'],
                    payment_date=date.today(),
                    expected_amount=Decimal(str(payment_info['expected_amount'])),
                    actual_amount=Decimal('0.00'),
                    payment_day=payment_info['payment_day'],
                    recorded_by=1,  # System user (admin)
                    notes="Auto-created payment record"
                )
                
                db.session.add(new_payment)
                created_count += 1
            
            db.session.commit()
            logger.info(f"Auto-created {created_count} payment records")
            return created_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error auto-creating payment records: {str(e)}")
            return 0

class SalaryAutomation:
    """Handles automated salary calculations"""
    
    @staticmethod
    def calculate_monthly_salaries(year, month):
        """Calculate salaries for all account officers for a specific month"""
        try:
            # Get all account officers
            account_officers = User.query.filter_by(role='account_officer', is_active=True).all()
            calculation_period = f"{year}-{month:02d}"
            
            calculated_count = 0
            
            for officer in account_officers:
                # Check if salary already calculated for this period
                existing_calc = SalaryCalculation.query.filter_by(
                    user_id=officer.id,
                    calculation_period=calculation_period
                ).first()
                
                if existing_calc:
                    continue  # Skip if already calculated
                
                # Calculate collections for the month
                start_date = date(year, month, 1)
                if month == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, month + 1, 1) - timedelta(days=1)
                
                # Get total collections for this officer's loans
                total_collections = db.session.query(func.sum(Payment.actual_amount)).join(Loan).filter(
                    Loan.account_officer_id == officer.id,
                    Payment.payment_date >= start_date,
                    Payment.payment_date <= end_date
                ).scalar() or Decimal('0.00')
                
                # Get default salary settings
                from settings import SystemSetting
                base_salary = Decimal(SystemSetting.get_setting('base_salary_default', '50000.00'))
                commission_rate = Decimal(SystemSetting.get_setting('commission_rate_default', '5.00'))
                
                # Create salary calculation
                salary_calc = SalaryCalculation(
                    user_id=officer.id,
                    calculation_period=calculation_period,
                    base_salary=base_salary,
                    commission_rate=commission_rate,
                    total_collections=total_collections
                )
                
                # Calculate commission and total salary
                salary_calc.calculate_commission()
                salary_calc.calculate_total_salary()
                
                db.session.add(salary_calc)
                calculated_count += 1
                
                logger.info(f"Calculated salary for {officer.full_name}: "
                          f"Base: {base_salary}, Collections: {total_collections}, "
                          f"Commission: {salary_calc.commission_amount}, Total: {salary_calc.total_salary}")
            
            db.session.commit()
            logger.info(f"Calculated salaries for {calculated_count} officers")
            return calculated_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error calculating monthly salaries: {str(e)}")
            return 0
    
    @staticmethod
    def calculate_current_month_salaries():
        """Calculate salaries for the current month"""
        today = date.today()
        return SalaryAutomation.calculate_monthly_salaries(today.year, today.month)

class ReportAutomation:
    """Handles automated report generation"""
    
    @staticmethod
    def generate_daily_summary():
        """Generate daily summary report"""
        try:
            today = date.today()
            
            # Get today's payments
            today_payments = Payment.query.filter_by(payment_date=today).all()
            total_expected = sum(payment.expected_amount for payment in today_payments)
            total_collected = sum(payment.actual_amount for payment in today_payments)
            
            # Get loan statistics
            total_loans = Loan.query.count()
            active_loans = Loan.query.filter_by(status='active').count()
            overdue_loans = Loan.query.filter_by(status='overdue').count()
            completed_today = Loan.query.filter_by(actual_end_date=today).count()
            
            summary = {
                'date': today.isoformat(),
                'payments': {
                    'total_expected': float(total_expected),
                    'total_collected': float(total_collected),
                    'collection_rate': float(total_collected / total_expected * 100) if total_expected > 0 else 0,
                    'payment_count': len(today_payments)
                },
                'loans': {
                    'total_loans': total_loans,
                    'active_loans': active_loans,
                    'overdue_loans': overdue_loans,
                    'completed_today': completed_today
                }
            }
            
            logger.info(f"Generated daily summary for {today}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {str(e)}")
            return None

def run_daily_automation():
    """Run all daily automation tasks"""
    logger.info("Starting daily automation tasks...")
    
    # Update loan statuses
    PaymentAutomation.update_all_loan_statuses()
    
    # Identify overdue loans
    PaymentAutomation.identify_overdue_loans()
    
    # Auto-create payment records for today
    PaymentAutomation.auto_create_payment_records()
    
    # Generate daily summary
    ReportAutomation.generate_daily_summary()
    
    logger.info("Daily automation tasks completed")

def run_monthly_automation():
    """Run monthly automation tasks"""
    logger.info("Starting monthly automation tasks...")
    
    # Calculate salaries for current month
    SalaryAutomation.calculate_current_month_salaries()
    
    logger.info("Monthly automation tasks completed")

