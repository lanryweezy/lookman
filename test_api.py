import requests
import json

BASE_URL = "http://127.0.0.1:5001/api"

def login(session):
    """Logs in the admin user and returns the session."""
    login_data = {"username": "admin", "password": "admin123"}
    response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    response.raise_for_status()
    print("Logged in successfully.")
    return response.json()

def create_borrower(session):
    """Creates a new borrower."""
    borrower_data = {
        "name": "Test Borrower",
        "phone": "9876543210",
        "address": "456 Test St",
    }
    response = session.post(f"{BASE_URL}/borrowers/", json=borrower_data)
    response.raise_for_status()
    print("Borrower created successfully.")
    return response.json()["borrower"]

def create_loan(session, borrower_id):
    """Creates a new loan for the given borrower."""
    loan_data = {
        "borrower_id": borrower_id,
        "principal_amount": 5000,
        "loan_duration_days": 15,
        "start_date": "2025-08-01",
    }
    response = session.post(f"{BASE_URL}/loans/", json=loan_data)
    response.raise_for_status()
    print("Loan created successfully.")
    return response.json()["loan"]

if __name__ == "__main__":
    with requests.Session() as session:
        login(session)
        borrower = create_borrower(session)
        loan = create_loan(session, borrower["id"])
        print("\n--- Test Results ---")
        print(f"Borrower: {json.dumps(borrower, indent=2)}")
        print(f"Loan: {json.dumps(loan, indent=2)}")
