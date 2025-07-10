# Lookman Loan Management System - Database Schema Design

## Database Tables and Relationships

### 1. Users Table
- **id**: Primary Key (Integer, Auto-increment)
- **username**: Unique username (String, 50 chars, Not Null)
- **password_hash**: Hashed password (String, 255 chars, Not Null)
- **full_name**: Full name of the user (String, 100 chars, Not Null)
- **role**: User role (Enum: 'admin', 'account_officer', Default: 'account_officer')
- **is_active**: Account status (Boolean, Default: True)
- **created_at**: Account creation timestamp (DateTime, Default: Now)
- **updated_at**: Last update timestamp (DateTime, Default: Now)

### 2. Borrowers Table
- **id**: Primary Key (Integer, Auto-increment)
- **name**: Borrower's full name (String, 100 chars, Not Null)
- **phone**: Phone number (String, 20 chars)
- **address**: Address (Text)
- **created_by**: Foreign Key to Users.id (Integer, Not Null)
- **created_at**: Record creation timestamp (DateTime, Default: Now)
- **updated_at**: Last update timestamp (DateTime, Default: Now)

### 3. Loans Table
- **id**: Primary Key (Integer, Auto-increment)
- **borrower_id**: Foreign Key to Borrowers.id (Integer, Not Null)
- **account_officer_id**: Foreign Key to Users.id (Integer, Not Null)
- **principal_amount**: Principal loan amount (Decimal, 10,2, Not Null)
- **interest_rate**: Interest rate percentage (Decimal, 5,2, Default: 0.00)
- **interest_amount**: Calculated interest amount (Decimal, 10,2, Default: 0.00)
- **expenses**: Loan processing expenses (Decimal, 10,2, Default: 0.00)
- **total_amount**: Total amount to be repaid (Decimal, 10,2, Not Null)
- **daily_repayment**: Daily repayment amount (Decimal, 10,2, Not Null)
- **loan_duration_days**: Duration in days (Integer, Default: 15)
- **start_date**: Loan start date (Date, Not Null)
- **expected_end_date**: Expected completion date (Date, Not Null)
- **actual_end_date**: Actual completion date (Date, Nullable)
- **status**: Loan status (Enum: 'active', 'completed', 'overdue', 'defaulted', Default: 'active')
- **created_at**: Record creation timestamp (DateTime, Default: Now)
- **updated_at**: Last update timestamp (DateTime, Default: Now)

### 4. Payments Table
- **id**: Primary Key (Integer, Auto-increment)
- **loan_id**: Foreign Key to Loans.id (Integer, Not Null)
- **payment_date**: Date of payment (Date, Not Null)
- **expected_amount**: Expected payment amount (Decimal, 10,2, Not Null)
- **actual_amount**: Actual payment amount (Decimal, 10,2, Default: 0.00)
- **payment_day**: Day number in the loan cycle (Integer, Not Null)
- **is_weekend_adjusted**: Whether payment was adjusted for weekend (Boolean, Default: False)
- **recorded_by**: Foreign Key to Users.id (Integer, Not Null)
- **notes**: Payment notes (Text, Nullable)
- **created_at**: Record creation timestamp (DateTime, Default: Now)
- **updated_at**: Last update timestamp (DateTime, Default: Now)

### 5. Salary_Calculations Table
- **id**: Primary Key (Integer, Auto-increment)
- **user_id**: Foreign Key to Users.id (Integer, Not Null)
- **calculation_period**: Period for calculation (String, 20 chars, e.g., '2024-01')
- **base_salary**: Base salary amount (Decimal, 10,2, Default: 0.00)
- **commission_rate**: Commission rate percentage (Decimal, 5,2, Default: 0.00)
- **total_collections**: Total collections for the period (Decimal, 10,2, Default: 0.00)
- **commission_amount**: Calculated commission (Decimal, 10,2, Default: 0.00)
- **total_salary**: Total salary (base + commission) (Decimal, 10,2, Default: 0.00)
- **created_at**: Record creation timestamp (DateTime, Default: Now)

### 6. System_Settings Table
- **id**: Primary Key (Integer, Auto-increment)
- **setting_key**: Setting name (String, 50 chars, Unique, Not Null)
- **setting_value**: Setting value (Text, Not Null)
- **description**: Setting description (Text)
- **updated_by**: Foreign Key to Users.id (Integer, Not Null)
- **updated_at**: Last update timestamp (DateTime, Default: Now)

## Relationships

1. **Users** (1) → (Many) **Borrowers** (created_by)
2. **Users** (1) → (Many) **Loans** (account_officer_id)
3. **Users** (1) → (Many) **Payments** (recorded_by)
4. **Users** (1) → (Many) **Salary_Calculations** (user_id)
5. **Users** (1) → (Many) **System_Settings** (updated_by)
6. **Borrowers** (1) → (Many) **Loans** (borrower_id)
7. **Loans** (1) → (Many) **Payments** (loan_id)

## Indexes for Performance

1. **Users**: username (unique), role
2. **Borrowers**: name, created_by
3. **Loans**: borrower_id, account_officer_id, status, start_date
4. **Payments**: loan_id, payment_date, recorded_by
5. **Salary_Calculations**: user_id, calculation_period

## Default System Settings

- **default_loan_duration**: 15 (days)
- **default_interest_rate**: 10.00 (percentage)
- **weekend_payment_handling**: 'next_business_day'
- **base_salary_default**: 50000.00
- **commission_rate_default**: 5.00 (percentage)

