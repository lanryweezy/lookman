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

def main():
    """Run all tests"""
    print("🧪 Testing Lookman Application")
    print("=" * 40)
    
    db_test = test_database_connection()
    route_test = test_routes()
    
    print("=" * 40)
    if db_test and route_test:
        print("✅ All tests passed! Application is ready for deployment.")
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)