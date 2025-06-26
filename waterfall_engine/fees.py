
from typing import Dict, List, Optional
from .models import ApplyRevenueDueResult, PaymentContext

from .settings import FREQ_MULTIPLIER


### FEE ###
class Fee:
    """
        Parameters
        ----------
        name : str
            Name of the fee.
        fee_config : dict
            Configuration of the fee (e.g., fixed amount, annual percentage).
        payment_frequency : str
            Frequency of payments (e.g., 'M' for monthly, 'Q' for quarterly).
        annual : bool
            Whether the fee is annual or not.
        payment_periods : list[int] | None
            Specific periods when the fee is due. If None, applies every period.    

        """
    def __init__(self, name: str, fee_config: dict, 
                 payment_frequency: str, annual: bool = False, 
                 payment_periods: Optional[List[int]] = None):
        
        self._name = name

        if fee_config.get('type') not in ['dollar_amount', 'percentage']:
            raise ValueError('Invalid fee config')

        self.fee_config = fee_config

        if payment_frequency not in ['M', 'Q', 'S', 'Y']:
            raise ValueError('Invalid payment frequency')
        self.payment_frequency = payment_frequency

        self.annual = annual
        self.payment_periods = payment_periods

        ### Last period 
        self._last_period_due = 0.0
        self._last_period_paid = 0.0
        self._last_period_unpaid = 0.0

        ### Totals
        self._total_paid = 0.0
        self._total_unpaid = 0.0
        
        ### History
        self.history = []
    
    def __repr__(self):
        return f"<Fee {self.name}: Last Due={self.last_period_due}, Total Paid={self.total_paid}>"

    ### PROPERTY
    @property
    def name(self):
        return self._name
    
    @property
    def last_period_due(self):
        return self._last_period_due
    
    @property
    def last_period_paid(self):
        return self._last_period_paid
    
    @property
    def last_period_unpaid(self):
        return self._last_period_unpaid
    
    @property
    def total_paid(self):
        return self._total_paid
    
    @property
    def total_unpaid(self):
        return self._total_unpaid

    def amount_due(self, pool_balance: float, period: int) -> float:
        """
        Calculates amount due this period for the fee.
        """
        if self.payment_periods is not None and period not in self.payment_periods:
            return 0.0
        
        if self.fee_config['type'] == 'dollar_amount':
            dollar_amount_due = self.fee_config['amount']
        else:
            dollar_amount_due = self.fee_config['amount'] * pool_balance
        
        if self.annual:
            multiplier = FREQ_MULTIPLIER.get(self.payment_frequency)
            return dollar_amount_due / multiplier
        else:
            return dollar_amount_due
    
    def apply_revenue_due(self, payment_context: PaymentContext, period: int) -> ApplyRevenueDueResult: 
        """
        Applies payment and tracks unpaid portion.
        """
        available_revenue_funds = payment_context.available_revenue_collections
        pool_balance = payment_context.pool_balance

        due = self.amount_due(pool_balance, period)
        paid = min(available_revenue_funds, due)
        unpaid = due - paid

        payment_run_return_payload = {
            'amount_due': due,
            'revenue_funds_distributed' : paid,
            'revenue_amount_unpaid' : unpaid,
        }
               
        return ApplyRevenueDueResult(**payment_run_return_payload)
    

    ### UPDATES 
    def update_history_revenue_distributions(self, period: int, due: float, paid: float, unpaid: float):
        self.history.append({
                'period': period, 
                'amount_due': due,
                'amount_paid': paid, 
                'amount_unpaid': unpaid
                })
        
    def update_last_period(self, due: float, paid: float, unpaid: float):
        self._last_period_due = due
        self._last_period_paid = paid
        self._last_period_unpaid = unpaid

    def update_totals(self, paid: float, unpaid: float):
        self._total_paid += paid
        self._total_unpaid += unpaid
