
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tranche import Tranche
    from .fees import Fee
    from .reserve import NonLiquidityReserve
    from .models import RevenueWaterfallLimb, RedemptionWaterfallLimb


### DEAL CLASS ###
class Deal:
    """
    Represents a securitization deal with its tranches, fees, and waterfalls.
    Contains methods to manage the deal's financial flows and history.
    """
    def __init__(self, 
                name: str, 
                tranches: 'list[Tranche]', 
                fees: 'list[Fee]', 
                reserve: 'NonLiquidityReserve',
                repayment_structure: str,
                revenue_waterfall_limbs: 'dict[int, RevenueWaterfallLimb]', 
                redemption_waterfall_limbs: 'dict[int, RedemptionWaterfallLimb]'
                ):
        
        self.name = name
        self.tranches = tranches
        self.fees = fees
        self.reserve = reserve

        if repayment_structure not in ['sequential', 'pro-rata']:
            raise ValueError('Invalid repayment structure. Must be "sequential" or "pro-rata".')
        self.repayment_structure = repayment_structure

        self.revenue_waterfall_limbs = revenue_waterfall_limbs
        self.redemption_waterfall_limbs = redemption_waterfall_limbs

        self.history_revenue = []
        self.history_redemption = []
