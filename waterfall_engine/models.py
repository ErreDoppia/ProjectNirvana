
from dataclasses import dataclass, field

##### UNIFIED WATERFALL

from abc import ABC, abstractmethod
from typing import TypedDict, Dict
from dataclasses import dataclass, field
from enum import Enum



### RESULT DATA STRUCTURES ###
class ApplyAmountDueResult(TypedDict):
    """
    Represents the result of a apply_revenue_due method.
    Contains the amount of funds distributed and any unpaid amounts.
    """
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
    raw_payment_context: RawPaymentContext
    
    last_period_tranche_ending_balance_total: float
    last_period_liquidity_reserve_balance: float
    
    available_cash: float

    #defaults 
    principal_allocations: Dict[str, float] = field(default_factory=dict)    
    shortfall: float = field(default_factory=float)

    #accessing RawPaymentContext attributes
    @property
    def pool_balance(self):
        return self.raw_payment_context.pool_balance

    @property
    def revenue_collections(self):
        return self.raw_payment_context.revenue_collections

    @property
    def redemption_collections(self):
        return self.raw_payment_context.redemption_collections        
    
    def __getitem__(self, key):
        return getattr(self, key)


### BASE ABSTRACT INTERFACES ###
class WaterfallLimb(ABC):
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
    def apply_amount_due(self, *args, **kwargs) -> ApplyAmountDueResult:
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

### WATERFALL WRAPPERS ###
class WaterfallProcessor(WaterfallLimb):
    """
    Processor for Revenue Waterfall limbs, wrapping Tranche logic.
    """
    def __init__(self, limb: WaterfallLimb):
        if not (hasattr(limb, 'name') or not hasattr(limb, 'apply_amount_due') 
                or not hasattr(limb, 'update_history_revenue_distributions') 
                or not hasattr(limb, 'update_last_period') or not hasattr(limb,'update_totals')):
            raise ValueError("Limb must have 'apply_amount_due' method and 'name' property.")
        self._limb = limb

    @property
    def name(self):
        return self._limb.name

    def apply_amount_due(self, payment_context: RawPaymentContext, period: int, waterfall_type) -> ApplyAmountDueResult:
        return self._limb.apply_amount_due(payment_context, period, waterfall_type)
    
    def update_history_revenue_distributions(self, period: int, due: float, paid: float, unpaid: float):
        """
        Updates the history of payments for this limb.
        """
        self._limb.update_history_revenue_distributions(period, due, paid, unpaid)

    def update_last_period(self, due: float, paid: float, unpaid: float):
        self._limb.update_last_period
    
    def update_totals(self, paid: float, unpaid: float):
        self._limb.update_totals


class WaterfallLimbResult(TypedDict):
    """
    Represents the result of a waterfall limb distribution (apply method).
    Contains the available cash, amount paid, and amount unpaid.
    """
    available_cash: float
    amount_due: float
    amount_paid: float
    amount_unpaid: float

