
from .models import RevenueWaterfallLimb, RevenuePaymentRunResult
from .settings import FREQ_MULTIPLIER

# Represents a fixed or percentage-based fee in the waterfall
class Fee(RevenueWaterfallLimb):
    def __init__(self, name: str, fee_config: dict, 
                 payment_frequency: str, annual: bool = False, 
                 payment_periods=None):
        """
        Parameters
        ----------
        name : str
            Name of the fee.
        fee_config : dict
            Configuration of the fee (e.g., fixed amount, annual percentage).
        """
        self._name = name

        if fee_config.get('type') not in ['dollar_amount', 'percentage']:
            raise ValueError('Invalid fee config')
        else:
            self.fee_config = fee_config

        if payment_frequency not in ['M', 'Q', 'S', 'Y']:
            raise ValueError('Invalid payment frequency')
        else:
            self.payment_frequency = payment_frequency

        self.annual = annual
        self.payment_periods = payment_periods
        
        self.total_paid = 0.0
        self.total_unpaid = 0.0
        self.history = []
    
    @property
    def name(self):
        """Returns the name of the fee."""
        return self._name
    
    def amount_due(self, pool_balance: float, period: int) -> float:
        """
        Calculates amount due this period for the fee.
        """
        if self.payment_periods and period not in self.payment_periods:
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
    
    def distribute_due(self, payment_context: dict, period: int) -> RevenuePaymentRunResult: 
        """
        Applies payment and tracks unpaid portion.
        """
        available_revenue_funds = payment_context.get('available_revenue_collections',0.0)
        pool_balance = payment_context.get('pool_balance', 0.0)

        due = self.amount_due(pool_balance, period)
        paid = min(available_revenue_funds, due)
        unpaid = due - paid
        
        self.total_paid += paid
        self.total_unpaid += unpaid

        payment_run_return_payload = {
            'revenue_funds_distributed' : paid,
            'revenue_amount_unpaid' : unpaid,
        }
               
        self.history.append([paid, unpaid])

        return payment_run_return_payload