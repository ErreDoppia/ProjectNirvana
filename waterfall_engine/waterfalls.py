 
from .models import PaymentContext, RevenueWaterfallLimb, RedemptionWaterfallLimb


### REVENUE AND REDEMPTION WATERFALLS ###
class RevenueWaterfall:
    """
    Revenue waterfall logic for payment allocation in RunWaterfall engine.
    """
    def __init__(self, waterfall_limbs: dict[int, RevenueWaterfallLimb]):
        """
        Initialize with an ordered dictionary of waterfall limbs.
        """
        self.limbs = waterfall_limbs
        
    def apply(self, payment_context: PaymentContext, period: int) -> dict[str, dict[str, float]]:
        """
        Applies collections to each limb by priority.
        """
        results = {}
            
        for priority, limb in self.limbs.items(): 
            name = limb.name
            payment_run_payload = limb.distribute_due(payment_context, period)
            
            revenue_funds_distributed = payment_run_payload.get('revenue_funds_distributed')
            amount_unpaid = payment_run_payload.get('revenue_amount_unpaid')
            
            results[f"{priority} - {name}"] = {
                'available_cash': payment_context.available_revenue_collections,
                'amount_paid': revenue_funds_distributed,
                'amount_unpaid': amount_unpaid
                }
            
            payment_context.available_revenue_collections = max(
                payment_context.available_revenue_collections - revenue_funds_distributed, 0)
        
        results['excess_spread'] = {
            'available_cash': payment_context.available_revenue_collections,
            'amount_paid': payment_context.available_revenue_collections,
            'amount_unpaid': 0.00
            }
        return results  


class RedemptionWaterfall:
    """
    Redemption waterfall logic for payment allocation in RunWaterfall engine.
    """
    def __init__(self, waterfall_limbs: dict[int, RedemptionWaterfallLimb]):
        """
        Initialize with an ordered dictionary of waterfall limbs.
        """
        self.limbs = waterfall_limbs
        
    def apply(self, payment_context: PaymentContext, period: int) -> dict[str, dict[str, float]]:
        """
        Applies collections to each limb by priority.
        """
        results = {}
            
        for priority, limb in self.limbs.items(): 
            name = limb.name
            payment_run_payload = limb.distribute_principal_due(payment_context, period)
            
            redemption_funds_distributed = payment_run_payload.get('redemption_funds_distributed')
            amount_unpaid = payment_run_payload.get('redemption_amount_unpaid')

            results[f"{priority} - {name}"] = {
                'available_cash': payment_context.available_redemption_collections,
                'amount_paid': redemption_funds_distributed,
                'amount_unpaid': amount_unpaid
                }
            
            payment_context.available_redemption_collections = max(
                payment_context.available_redemption_collections - redemption_funds_distributed, 0.0)

        results['excess_spread'] = {
            'available_cash': payment_context.available_redemption_collections,
            'amount_paid': payment_context.available_redemption_collections,
            'amount_unpaid': 0.00
            }
        
        return results