

from .tranche import Tranche
from .fees import Fee
from .models import RevenueWaterfallLimb, RedemptionWaterfallLimb
from .waterfalls import RevenueWaterfall, RedemptionWaterfall
from .models import RevenuePaymentRunResult, RedemptionPaymentRunResult
from .models import PaymentContext

### DEAL CLASS ###
class Deal:
    """
    Represents a securitization deal with its tranches, fees, and waterfalls.
    Contains methods to manage the deal's financial flows and history.
    """
    def __init__(self, 
                name: str, 
                tranches: list[Tranche], 
                fees: list[Fee], 
                repayment_structure: str,
                revenue_waterfall_limbs: dict[int, RevenueWaterfallLimb], 
                redemption_waterfall_limbs: dict[int, RedemptionWaterfallLimb]
                ):
        
        self.name = name
        self.tranches = tranches
        self.fees = fees

        if repayment_structure not in ['sequential', 'pro-rata']:
            raise ValueError('Invalid repayment structure. Must be "sequential" or "pro-rata".')
        self.repayment_structure = repayment_structure

        self.revenue_waterfall_limbs = revenue_waterfall_limbs
        self.redemption_waterfall_limbs = redemption_waterfall_limbs

        self.revenue_waterfall = RevenueWaterfall(self.revenue_waterfall_limbs)
        self.redemption_waterfall = RedemptionWaterfall(self.redemption_waterfall_limbs)

        self._total_initial_balance = sum(t.initial_balance for t in self.tranches)

        self._total_last_period_ending_balance = sum(t.last_period_ending_balance for t in self.tranches)

        self.history_revenue = []
        self.history_redemption = []

    @property
    def total_initial_balance(self) -> float:
        """
        Returns the total initial balance of all tranches.
        """
        return self._total_initial_balance
    
    @property
    def total_last_period_ending_balance(self) -> float:
        """
        Returns the total last period ending balance of all tranches.
        """
        return self._total_last_period_ending_balance
    
    def update_total_last_period_ending_balance(self):
        """
        Updates the total last period ending balance based on current tranche balances.
        """
        self._total_last_period_ending_balance = sum(t.last_period_ending_balance for t in self.tranches)