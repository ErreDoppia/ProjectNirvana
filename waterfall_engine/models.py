
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TypedDict, Dict



### RESULT DATA STRUCTURES ###
class RevenuePaymentRunResult(TypedDict):
    revenue_funds_distributed: float
    revenue_amount_unpaid: float

class RedemptionPaymentRunResult(TypedDict):
    redemption_funds_distributed: float
    redemption_amount_unpaid: float

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
    def distribute_due(self, *args, **kwargs) -> RevenuePaymentRunResult:
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
    def distribute_principal_due(self, *args, **kwargs) -> RedemptionPaymentRunResult:
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

