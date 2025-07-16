from .user import db, User
from .borrowers import Borrower
from .loans import Loan
from .payments import Payment
from .salary import SalaryCalculation
from .settings import SystemSetting

__all__ = ['db', 'User', 'Borrower', 'Loan', 'Payment', 'SalaryCalculation', 'SystemSetting']

