
from math import isclose

from .models import RevenueWaterfallLimb, RedemptionWaterfallLimb

def ensure_weights_sum_to_one(weights: dict[str, float]) -> None:
    """
    Ensure that the sum of weights is approximately equal to 1.0.
    Raises ValueError if the sum deviates significantly from 1.0.
    """
    total_weight = sum(weights.values())
    if not isclose(total_weight, 1.0, abs_tol=1e-8):
        raise ValueError(f"Weights do not sum to 1.0, current sum: {total_weight}. Check tranche balances.")
    

def wrap_revenue_waterfall_limb(limb: 'RevenueWaterfallLimb') -> 'RevenueWaterfallLimb':
    """
    Wraps a RevenueWaterfallLimb instance to ensure it has the required methods.
    """
    if not hasattr(limb, 'distribute_due') or not hasattr(limb, 'name'):
        raise ValueError("Limb must have 'distribute_due' method and 'name' property.")
    return limb


def wrap_redemption_waterfall_limb(limb: 'RedemptionWaterfallLimb') -> 'RedemptionWaterfallLimb':
    """
    Wraps a RedemptionWaterfallLimb instance to ensure it has the required methods.
    """
    if not hasattr(limb, 'distribute_principal_due') or not hasattr(limb, 'name'):
        raise ValueError("Limb must have 'distribute_principal_due' method and 'name' property.")
    return limb