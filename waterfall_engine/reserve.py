
from waterfall_engine.models import ApplyAmountDueResult, PaymentContext


"""
Reserves:
RMBS
K- liq reserve percentage of Class A initial balanace
SOCK - total reserve percetange of CE notes = liq res + non liq res. Liq Res = percentage of class A. Non liq = total - liq

TB - liq resever percentage of A and B initial balance, then last balance, then when A and B redeem 0. 
Credit = Total - liq. Total = percentage of the initial balance of the collateralised notes 

CMBS
MAGR - general reserve - percentage of all notes
"""

class TotalReserve:
    """
    """
    def __init__(self) -> None:
        pass


class LiquidityReserve:
    def __init__(self) -> None:
        pass


class NonLiquidityReserve:
    def __init__(self, name: str, initial_balance: float, required_percentage: float, method: str) -> None:
        self._name = name
        self.required_percentage = required_percentage

        if method not in ["pool_balance", "last_period_total_tranche_balance"]:
            raise ValueError("Invalid Method")
        
        self.method = method

        self.initial_balance = initial_balance

        self._last_period_balance = initial_balance
        self.history = []

    @property
    def name(self):
        return self._name
    
    @property
    def last_period_balance(self):
        return self._last_period_balance
    
    def apply_amount_due(self, payment_context: PaymentContext, period: int, waterfall_type: str) -> ApplyAmountDueResult:

        available_revenue_funds = payment_context.available_cash
        due = self.get_required_amount(payment_context)
        paid = min(available_revenue_funds, due)
        unpaid = due - paid

        payment_run_return_payload = {
            'amount_due': due,
            'amount_paid' : paid,
            'amount_unpaid' : unpaid,
        }   
        return ApplyAmountDueResult(**payment_run_return_payload)

    def get_required_amount(self, payment_context: PaymentContext):
        return round(self.required_percentage * payment_context.last_period_tranche_ending_balance_total,2)
    
    def update_history_revenue_distributions(self, period: int, due: float, paid: float, unpaid: float):
            self.history.append({
                'period': period, 
                'amount_due': due,
                'amount_paid': paid, 
                'amount_unpaid': unpaid
                })
            
    def update_last_period_balance(self, paid: float):
        self._last_period_balance = paid