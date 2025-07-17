#!/usr/bin/env python3
"""
Simple test script for Lookman application
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from user import db, User
from borrowers import Borrower
from loans import Loan
from payments import Payment
from settings import SystemSetting
from main import app

def test_database_connection():
    """Test database connection and models"""
    try:
        with app.app_context():
            # Test database connection
            db.create_all()
            print("✅ Database connection successful")
            
            # Test user creation
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                print("✅ Admin user exists")
            else:
                print("❌ Admin user not found")
            
            # Test model counts
            user_count = User.query.count()
            borrower_count = Borrower.query.count()
            loan_count = Loan.query.count()
            payment_count = Payment.query.count()
            
            print(f"📊 Database stats:")
            print(f"   Users: {user_count}")
            print(f"   Borrowers: {borrower_count}")
            print(f"   Loans: {loan_count}")
            print(f"   Payments: {payment_count}")
            
            return True
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False

def test_routes():
    """Test basic routes"""
    try:
        with app.test_client() as client:
            # Test home route
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Home route working")
            else:
                print(f"❌ Home route failed: {response.status_code}")
            
            # Test API health check
            response = client.get('/api/auth/check-auth')
            if response.status_code in [200, 401]:  # 401 is expected when not logged in
                print("✅ API routes working")
            else:
                print(f"❌ API routes failed: {response.status_code}")
            
            return True
    except Exception as e:
        print(f"❌ Route test failed: {str(e)}")
        return False

def test_create_borrower():
    """Test creating a new borrower"""
    try:
        with app.test_client() as client:
            # Login first
            client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})

            borrower_data = {
                "name": "Unit Test Borrower",
                "phone": "1112223333",
                "address": "789 Unit Test Ave"
            }
            response = client.post('/api/borrowers/', json=borrower_data)

            if response.status_code == 201:
                print("✅ Borrower creation test passed")
                return True
            else:
                print(f"❌ Borrower creation test failed: {response.status_code} - {response.get_data(as_text=True)}")
                return False
    except Exception as e:
        print(f"❌ Borrower creation test failed: {str(e)}")
        return False

def test_create_loan():
    """Test creating a new loan"""
    try:
        with app.test_client() as client:
            # Login first
            client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})

            # Create a borrower first
            borrower_data = {
                "name": "Loan Test Borrower",
                "phone": "4445556666",
                "address": "101 Loan Test Ln"
            }
            borrower_response = client.post('/api/borrowers/', json=borrower_data)
            borrower_id = borrower_response.get_json()['borrower']['id']

            loan_data = {
                "borrower_id": borrower_id,
                "principal_amount": 10000,
                "loan_duration_days": 20,
                "start_date": "2025-09-01"
            }
            response = client.post('/api/loans/', json=loan_data)

            if response.status_code == 201:
                print("✅ Loan creation test passed")
                return True
            else:
                print(f"❌ Loan creation test failed: {response.status_code} - {response.get_data(as_text=True)}")
                return False
    except Exception as e:
        print(f"❌ Loan creation test failed: {str(e)}")
        return False

def test_create_payment():
    """Test creating a new payment"""
    try:
        with app.test_client() as client:
            # Login first
            client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})

            # Create a borrower and a loan first
            borrower_data = {
                "name": "Payment Test Borrower",
                "phone": "7778889999",
                "address": "202 Payment Test Pl"
            }
            borrower_response = client.post('/api/borrowers/', json=borrower_data)
            borrower_id = borrower_response.get_json()['borrower']['id']

            loan_data = {
                "borrower_id": borrower_id,
                "principal_amount": 5000,
                "loan_duration_days": 10,
                "start_date": "2025-10-01"
            }
            loan_response = client.post('/api/loans/', json=loan_data)
            loan_id = loan_response.get_json()['loan']['id']

            payment_data = {
                "loan_id": loan_id,
                "payment_day": 1,
                "payment_date": "2025-10-01",
                "actual_amount": 500
            }
            response = client.post('/api/payments/', json=payment_data)

            if response.status_code == 201:
                print("✅ Payment creation test passed")
                return True
            else:
                print(f"❌ Payment creation test failed: {response.status_code} - {response.get_data(as_text=True)}")
                return False
    except Exception as e:
        print(f"❌ Payment creation test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Lookman Application")
    print("=" * 40)
    
    db_test = test_database_connection()
    route_test = test_routes()
    borrower_test = test_create_borrower()
    loan_test = test_create_loan()
    payment_test = test_create_payment()
    
    print("=" * 40)
    if db_test and route_test and borrower_test and loan_test and payment_test:
        print("✅ All tests passed! Application is ready for deployment.")
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)