
from abc import ABC, abstractmethod
from typing import TypedDict


### Base abstract interfaces ###
class RevenueWaterfallLimb(ABC):
    """
    Abstract base class representing a limb in the revenue waterfall.
    All limbs must implement the `distribute_due` method and `name` property.
    """
    
    @abstractmethod
    def distribute_due(self, *args, **kwargs) -> float:
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
    def distribute_principal_due(self, *args, **kwargs) -> float:
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

### Result data structures ###
class RevenuePaymentRunResult(TypedDict):
    revenue_funds_distributed: float
    revenue_amount_unpaid: float

class RedemptionPaymentRunResult(TypedDict):
    redemption_funds_distributed: float
    redemption_amount_unpaid: float
