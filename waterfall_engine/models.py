
from abc import ABC, abstractmethod
from typing import TypedDict, Dict
from dataclasses import dataclass, field


### RESULT DATA STRUCTURES ###
class ApplyRevenueDueResult(TypedDict):
    """
    Represents the result of a apply_revenue_due method.
    Contains the amount of funds distributed and any unpaid amounts.
    """
    amount_due: float
    revenue_funds_distributed: float
    revenue_amount_unpaid: float

class ApplyRedemptionDueResult(TypedDict):
    """
    Represents the result of a apply_redemption_due method.
    Contains the amount of funds distributed and any unpaid amounts.
    """
    redemption_funds_distributed: float
    redemption_amount_unpaid: float

class WaterfallLimbResult(TypedDict):
    """
    Represents the result of a waterfall limb distribution (apply method).
    Contains the available cash, amount paid, and amount unpaid.
    """
    available_cash: float
    amount_due: float
    amount_paid: float
    amount_unpaid: float   

### PAYMENT CONTEXT ###
@dataclass
class RawPaymentContext:
    revenue_collections: float
    redemption_collections: float
    pool_balance: float

@dataclass
class PaymentContext:
    payment_context: RawPaymentContext
    
    available_revenue_collections: float
    available_redemption_collections: float
    last_period_tranche_ending_balance_total: float
    last_period_liquidity_reserve_balance: float

    #defaults 
    principal_allocations: Dict[str, float] = field(default_factory=dict)    
    shortfall: float = field(default_factory=float)

    #accessing RawPaymentContext attributes
    @property
    def pool_balance(self):
        return self.payment_context.pool_balance

    @property
    def revenue_collections(self):
        return self.payment_context.revenue_collections

    @property
    def redemption_collections(self):
        return self.payment_context.redemption_collections
    

### BASE ABSTRACT INTERFACES ###
class RevenueWaterfallLimb(ABC):
    """
    Abstract base class representing a limb in the revenue waterfall.
    All limbs must implement the `distribute_due` method and `name` property.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the name identifier of the limb.
        """
        pass

    @abstractmethod
    def apply_revenue_due(self, *args, **kwargs) -> ApplyRevenueDueResult:
        """
        Processes the payment due for this limb in a given period.
        """
        pass

    @abstractmethod
    def update_history_revenue_distributions(self, period: int, due: float, paid: float, unpaid: float):
        """
        Updates the history of payments for this limb.
        This method can be overridden by subclasses to implement specific history tracking.
        """
        pass

    @abstractmethod
    def update_last_period(self, due: float, paid: float, unpaid: float):
        pass
    
    @abstractmethod
    def update_totals(self, paid: float, unpaid: float):
        pass
     

class RedemptionWaterfallLimb(ABC):
    """
    Abstract base class representing a limb in the redemption waterfall.
    All limbs must implement the `distribute_principal_due` method and `name` property.
    """
    
    @abstractmethod
    def apply_redemption_due(self, *args, **kwargs) -> ApplyRedemptionDueResult:
        """
        Processes the payment due for this limb in a given period.
        """
        pass

    @abstractmethod
    def update_history_redemption_distributions(self, period, paid, unpaid):
        """
        Updates the history of payments for this limb.
        This method can be overridden by subclasses to implement specific history tracking.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the name identifier of the limb.
        """

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

    def apply_revenue_due(self, payment_context: PaymentContext, period: int) -> ApplyRevenueDueResult:
        return self._limb.apply_revenue_due(payment_context, period)
    
    def update_history_revenue_distributions(self, period: int, due: float, paid: float, unpaid: float):
        """
        Updates the history of payments for this limb.
        """
        self._limb.update_history_revenue_distributions(period, due, paid, unpaid)

    def update_last_period(self, due: float, paid: float, unpaid: float):
        self._limb.update_last_period
    
    def update_totals(self, paid: float, unpaid: float):
        self._limb.update_totals

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

    def apply_redemption_due(self, payment_context: PaymentContext, period: int) -> ApplyRedemptionDueResult:
        return self._limb.apply_redemption_due(payment_context, period)
    
    def update_history_redemption_distributions(self, period: int, paid: float, unpaid: float):
        self._limb.update_history_redemption_distributions(period, paid, unpaid)
