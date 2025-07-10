from .user import db, User
from .borrower import Borrower
from .loan import Loan
from .payment import Payment
from .salary import SalaryCalculation
from .settings import SystemSetting

__all__ = ['db', 'User', 'Borrower', 'Loan', 'Payment', 'SalaryCalculation', 'SystemSetting']

