
from math import isclose

from .models import RawPaymentContext

def ensure_weights_sum_to_one(weights: dict[str, float]) -> None:
    """
    Ensure that the sum of weights is approximately equal to 1.0.
    Raises ValueError if the sum deviates significantly from 1.0.
    """
    total_weight = sum(weights.values())
    if not isclose(total_weight, 1.0, abs_tol=1e-8):
        raise ValueError(f"Weights do not sum to 1.0, current sum: {total_weight}. Check tranche balances.")
    

def get_limb_key(i: int, name: str) -> str:
    return f"{i} - {name}"

def get_watefall(waterfall_type: str, payment_context: RawPaymentContext):
    pass