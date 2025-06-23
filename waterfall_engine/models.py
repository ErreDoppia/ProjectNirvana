

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TypedDict, Dict


### RESULT DATA STRUCTURES ###
class RevenuePaymentRunResult(TypedDict):
    """
    Represents the result of a distribute_due method.
    Contains the amount of funds distributed and any unpaid amounts.
    """
    revenue_funds_distributed: float
    revenue_amount_unpaid: float

class RedemptionPaymentRunResult(TypedDict):
    """
    Represents the result of a distribute_principal_due method.
    Contains the amount of funds distributed and any unpaid amounts.
    """
    redemption_funds_distributed: float
    redemption_amount_unpaid: float

class WaterfallLimbResult(TypedDict):
    """
    Represents the result of a waterfall limb distribution.
    Contains the available cash, amount paid, and amount unpaid.
    """
    available_cash: float
    amount_paid: float
    amount_unpaid: float

### PAYMENT CONTEXT ###
@dataclass
class PaymentContext:
    available_revenue_collections: float
    available_redemption_collections: float
    pool_balance: float
    principal_allocations: Dict[str, float] = field(default_factory=dict)

### BASE ABSTRACT INTERFACES ###
class RevenueWaterfallLimb(ABC):
    """
    Abstract base class representing a limb in the revenue waterfall.
    All limbs must implement the `distribute_due` method and `name` property.
    """
    
    @abstractmethod
    def apply_revenue_due(self, *args, **kwargs) -> RevenuePaymentRunResult:
        """
        Processes the payment due for this limb in a given period.
        """
        pass
     
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the name identifier of the limb.
        """
        pass

class RedemptionWaterfallLimb(ABC):
    """
    Abstract base class representing a limb in the redemption waterfall.
    All limbs must implement the `distribute_principal_due` method and `name` property.
    """
    
    @abstractmethod
    def apply_redemption_due(self, *args, **kwargs) -> RedemptionPaymentRunResult:
        """
        Processes the payment due for this limb in a given period.
        """
        pass
     
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the name identifier of the limb.
        """

### WATERFALL WRAPPERS ###
class RevenueProcessor(RevenueWaterfallLimb):
    """
    Processor for Revenue Waterfall limbs, wrapping Tranche logic.
    """
    def __init__(self, limb: RevenueWaterfallLimb):
        if not hasattr(limb, 'apply_revenue_due') or not hasattr(limb, 'name'):
            raise ValueError("Limb must have 'apply_revenue_due' method and 'name' property.")
        self._limb = limb

    @property
    def name(self):
        return self._limb.name

    def apply_revenue_due(self, payment_context: PaymentContext, period: int) -> RevenuePaymentRunResult:
        return self._limb.apply_revenue_due(payment_context, period)

class RedemptionProcessor(RedemptionWaterfallLimb):
    """
    Processor for Redemption Waterfall limbs, wrapping Tranche logic.
    """
    def __init__(self, limb: RedemptionWaterfallLimb):
        if not hasattr(limb, 'apply_redemption_due') or not hasattr(limb, 'name'):
            raise ValueError("Limb must have 'apply_redemption_due' method and 'name' property.")
        self._limb = limb

    @property
    def name(self):
        return self._limb.name

    def apply_redemption_due(self, payment_context: PaymentContext, period: int) -> RedemptionPaymentRunResult:
        return self._limb.apply_redemption_due(payment_context, period)
