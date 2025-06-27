
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tranche import Tranche
    from .fees import Fee
    from .reserve import NonLiquidityReserve
    from .models import WaterfallLimb


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
                waterfalls: 'dict[str, dict[int, WaterfallLimb]]',
                ):
        
        self.name = name
        self.tranches = tranches
        self.fees = fees
        self.reserve = reserve

        if repayment_structure not in ['sequential', 'pro-rata']:
            raise ValueError('Invalid repayment structure. Must be "sequential" or "pro-rata".')
        self.repayment_structure = repayment_structure

        valid_keys = {'revenue', 'redemption'}
        if not set(waterfalls.keys()).issubset(valid_keys):
            raise ValueError('Invalid waterfall key. Must be "revenue" or "redemption".')
        
        self.waterfalls = waterfalls

        self.revenue_waterfall_limbs = waterfalls.get('revenue')
        self.redemption_waterfall_limbs = waterfalls.get('redemption')

        self.history_revenue = []
        self.history_redemption = []
