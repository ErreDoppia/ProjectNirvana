
from math import isclose
from typing import TYPE_CHECKING

from .settings import FREQ_MULTIPLIER

from .models import PaymentContext

if TYPE_CHECKING:
    from .tranche import Tranche

from .utils import ensure_weights_sum_to_one


### PRINCIPAL ALLOCATION RULES ###
class PrincipalAllocationRules:
    def __init__(self, tranches: 'list[Tranche]', repayment_structure: str):
        self.tranches = tranches
        self.repayment_structure = repayment_structure

    def get_sequential_weights(self, payment_context: PaymentContext) -> dict[str, float]:
        """
        Allocates principal repayments across tranches in a sequential manner.
        This method is currently not used but can be extended for future use.
        """
        available_funds = payment_context.available_cash
        allocation: dict[str, float] = {}

        last_period_ending_balance = [tranche.last_period_ending_balance for tranche in self.tranches]
            
        first_non_redeemed_tranche = next(
            (i for i, x in enumerate(last_period_ending_balance) if x > 0), 0
        )
        temp_weights = [0.0] * len(self.tranches)
        temp_weights[first_non_redeemed_tranche] = 1.0

        weights = {
            tranche.name: temp_weights[i] for i, tranche in enumerate(self.tranches)
        }

        # Ensure weights sum to 1
        ensure_weights_sum_to_one(weights)
        return weights
    
    def get_pro_rata_weights(self, payment_context: PaymentContext) -> dict[str, float]:
        """
        Allocates principal repayments across tranches in a pro-rata manner.
        This method is currently not used but can be extended for future use.
        """
        available_funds = payment_context.available_cash

        # Pro-rata allocation weights based on last period ending balance
        weights = {
            tranche.name: tranche.last_period_ending_balance / sum(t.last_period_ending_balance for t in self.tranches)
            for tranche in self.tranches
        }
        
        # Ensure weights sum to 1
        ensure_weights_sum_to_one(weights)

        return weights

    def allocate_principal(self, payment_context: PaymentContext) -> dict[str, float]:
        """
        Allocates principal repayments across tranches based on the defined structure.
        Currently supports only sequential allocation.
        """
        available_funds = payment_context.available_cash

        if self.repayment_structure == 'sequential':
            weights = self.get_sequential_weights(payment_context)
        elif self.repayment_structure == 'pro-rata':
            weights = self.get_pro_rata_weights(payment_context)
        elif self.repayment_structure == 'reverse-sequential':
            raise NotImplementedError("Reverse sequential allocation is not yet implemented.")
        else:
            raise ValueError(f"Unsupported repayment structure: {self.repayment_structure}")
        
        # Compute allocation
        desired_allocation = [round(available_funds * w, 2) for w in weights.values()]
        allocation = dict(zip(weights.keys(), desired_allocation))

        return allocation
    

class InterestAmountCalculation:
    """
    Class to handle interest calculations for a tranche.
    """
    @staticmethod
    def calculate(
        balance: float, interest_rate: float, 
        payment_frequency: str, method: str
        ) -> float:
        """
        Calculates the interest amount due based on the current balance and interest rates.
        """
        monthly_interest_rate = interest_rate / FREQ_MULTIPLIER[payment_frequency]
        interest_due = round(balance * monthly_interest_rate, 2)
        return interest_due