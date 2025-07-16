from flask import Blueprint, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date, timedelta

from user import db, User
from loans import Loan
from payments import Payment
from settings import SystemSetting

automation_bp = Blueprint('automation', __name__)

def update_loan_statuses():
    """
    Job to automatically update loan statuses from 'active' to 'overdue'
    if the expected end date has passed.
    """
    with db.app.app_context():
        try:
            today = date.today()

            # Get active loans where the expected end date is in the past
            overdue_loans = Loan.query.filter(
                Loan.status == 'active',
                Loan.expected_end_date < today
            ).all()
            
            for loan in overdue_loans:
                loan.status = 'overdue'
                loan.updated_at = datetime.utcnow()
            
            if overdue_loans:
                db.session.commit()
                print(f"Successfully updated {len(overdue_loans)} loans to 'overdue'.")
            else:
                print("No active loans to mark as overdue.")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error in update_loan_statuses job: {e}")

def setup_scheduler():
    """
    Initializes and starts the background scheduler.
    """
    scheduler = BackgroundScheduler(daemon=True)
    
    # Schedule the job to run once every day at midnight
    scheduler.add_job(
        update_loan_statuses,
        'cron',
        hour=0,
        minute=5,
        id='update_loan_statuses_job',
        replace_existing=True
    )
    
    try:
        scheduler.start()
        print("Scheduler started successfully.")
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")

# Example endpoint to manually trigger the job for testing
@automation_bp.route('/trigger-overdue-check', methods=['POST'])
def trigger_overdue_check():
    """
    Manually triggers the overdue loan status check.
    """
    try:
        update_loan_statuses()
        return jsonify({'message': 'Overdue loan check completed successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize the scheduler when the app starts
# This should be called from the main app factory if using one,
# or directly in the main script.
# For this example, we'll assume it's called from main.py.
# setup_scheduler()
