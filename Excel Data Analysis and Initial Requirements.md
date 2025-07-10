## Excel Data Analysis and Initial Requirements

### Excel Data Fields:
- **S/N**: Serial Number (likely unique identifier for each loan/borrower)
- **NAME**: Borrower's Name
- **DATE**: Loan Date (seems to be missing for most entries in the sample)
- **PRINCIPAL**: Principal loan amount
- **REPAYMENT AMOUNT**: Daily repayment amount
- **INTEREST**: Interest amount
- **EXPENSES**: Expenses related to the loan
- **INCOME**: Income from the loan
- **TOTAL**: Total amount (likely Principal + Interest + Expenses)
- **DAY 1** to **DAY 15**: Daily repayment entries. This suggests a fixed repayment period, but the user mentioned daily payments 

daily except for weekend. This needs clarification on the actual repayment period and how many days a loan typically runs.
- **SUB TOTAL**: Appears to be the sum of daily payments.
- **OUTSTANDING**: Remaining balance (only one non-null value in the sample).

### Observations and Inferred Requirements:
1.  **Loan Tracking**: The app needs to track individual loans, including principal, repayment amount, interest, expenses, and income.
2.  **Daily Payments**: The system must handle daily repayments, with a clear understanding of how weekends are managed (e.g., payments due on Monday if due on Saturday/Sunday).
3.  **User Management**: Admin should be able to create users (account officers) with names and passwords.
4.  **Admin Interface**: A dedicated interface for administrators to manage loans, users, and view overall financial data.
5.  **Account Officer Interface**: A separate interface for account officers to track their assigned loans and payments.
6.  **Automated Calculations**: The app should automatically calculate operational salaries and income.
7.  **Database**: SQL Alchemy is specified for database interaction.
8.  **Web-based**: The application should be accessible via a web browser.

### Clarification Needed from User:
1.  **Loan Repayment Period**: What is the typical or maximum duration of a loan? Is it always 15 days, or can it be longer? How are daily payments handled for weekends and public holidays?
2.  **Data Entry**: How will new loan data be entered into the system? Will it be manual entry by account officers or imported from another source?
3.  **User Roles**: Besides Admin and Account Officer, are there any other user roles with different permissions?
4.  **Salary Calculation**: What are the criteria for calculating operational salaries? Is it a fixed salary, commission-based, or a combination?
5.  **Income Calculation**: How is income calculated? Is it simply `TOTAL - PRINCIPAL - EXPENSES` or are there other factors?
6.  **Existing Data Migration**: Does the existing Excel data need to be migrated into the new system, or will the app start with fresh data?
7.  **Reporting**: What kind of reports are needed (e.g., daily collections, outstanding loans, profit/loss)?
8.  **Notifications**: Are there any notification requirements (e.g., payment reminders, overdue alerts)?


