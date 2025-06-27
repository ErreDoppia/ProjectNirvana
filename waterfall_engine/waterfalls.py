 
from .models import RawPaymentContext, WaterfallLimbResult
from .models import WaterfallLimb, WaterfallLimbResult, WaterfallProcessor
from .context import PaymentContextHandler 


### WATERFALLS ###
class WaterfallCalculator:
    """
    Revenue waterfall logic for payment allocation in RunWaterfall engine.
    """
    def __init__(self, waterfall_limbs: dict[int, WaterfallLimb]):
        """
        Initialize with an ordered dictionary of waterfall limbs.
        """
        self.limbs = waterfall_limbs
       
    def flush(self, payment_context: RawPaymentContext, period: int, waterfall_type: str) -> dict[str, WaterfallLimbResult]:
        """
        Applies collections to each limb by priority.
        """
        results = {}

        for priority, limb in self.limbs.items(): 
            name = limb.name
            payment_run_payload = limb.apply_amount_due(payment_context, period, waterfall_type)
            
            amount_paid = payment_run_payload.get('amount_paid') or 0.0 ### TODO Implement better value checks
            amount_unpaid = payment_run_payload.get('amount_unpaid')
            
            results[f"{priority} - {name}"] = {
                'available_cash': payment_context.available_cash,
                'amount_paid': amount_paid,
                'amount_unpaid': amount_unpaid
                }
            
            available_cash = payment_context.available_cash or 0.0

            payment_context.available_cash = max(available_cash - amount_paid, 0)
        
        results['surplus'] = {
            'available_cash': payment_context.available_cash or 0.0,
            'amount_paid': payment_context.available_cash or 0.0,
            'amount_unpaid': 0.00
            }
        return results  
