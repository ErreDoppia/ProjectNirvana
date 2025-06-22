
from typing import Optional
from abc import ABC, abstractmethod
from typing import TypedDict

from math import isclose

from .settings import FREQ_MULTIPLIER
from .tranche import Tranche
from .fees import Fee
from .deal import Deal
from .models import RevenueWaterfallLimb, RedemptionWaterfallLimb
from .models import RevenuePaymentRunResult, RedemptionPaymentRunResult
from .models import PaymentContext


### PRINCIPAL ALLOCATION RULES ###
class PrincipalAllocationRules:
    def __init__(self, deal: Deal):

        self.deal = deal

    def allocate_principal(self, payment_context: PaymentContext) -> dict[str, float]:
        """
        Allocates principal repayments across tranches based on the defined structure.
        Currently supports only sequential allocation.
        """

        available_funds = payment_context.available_redemption_collections
        tranches = self.deal.tranches
        allocation: dict[str, float] = {}

        if self.deal.repayment_structure == 'sequential':
            weights = {
                tranche.name: 1.0 for tranche in tranches if tranche.last_period_ending_balance > 0
            }
        else:
            # Pro-rata allocation weights based on last period ending balance
            weights = {
                tranche.name: tranche.last_period_ending_balance / self.deal.total_last_period_ending_balance
                for tranche in tranches
            }
            # Ensure weights sum to 1
            total_weight = sum(weights.values())
            if not isclose(total_weight, 1.0):
                raise ValueError("Weights do not sum to 1.0, check tranche balances.")
 
        # Compute allocation
        for tranche in tranches:
            desired_allocation = round(weights[tranche.name] * available_funds, 2)
            payment = min(tranche.last_period_ending_balance, desired_allocation)
            if payment > 0:
                allocation[tranche.name] = payment
                available_funds -= payment

        return allocation
     

### RUN WATERFALL ENGINE ###
class RunWaterfall:
    def __init__(self, deal: Deal):
        """
        Initialize the securitization deal with waterfall limbs and structure.
        """
        self.deal = deal
        
    def run_IPD(self, payment_context: PaymentContext, period: int):
        """
        Executes one Interest Payment Date logic.
        """
        principal_allocations = PrincipalAllocationRules(self.deal).allocate_principal(payment_context)
        payment_context.principal_allocations = principal_allocations

        if payment_context.principal_allocations == principal_allocations:
            # Apply revenue and redemption waterfalls
            rev_waterfall_results = self.deal.revenue_waterfall.apply(payment_context, period)
            red_waterfall_results = self.deal.redemption_waterfall.apply(payment_context, period)
        else:
            raise ValueError("Principal allocations do not match expected allocations.")
        
        snapshot_revenue = {period: rev_waterfall_results}
        snapshot_redemption = {period: red_waterfall_results}

        self.deal.history_revenue.append(snapshot_revenue)
        self.deal.history_redemption.append(snapshot_redemption)

        self.deal.update_total_last_period_ending_balance()

        print(f"IPD number {period}")
        print(f"Interest: {self.deal.history_revenue[period-1]}")
        print("")
        print(f"Principal: {self.deal.history_redemption[period-1]}")
        print("")
        
    def run_all_IPDs(self, payment_contexts: list[PaymentContext]):
        """
        Executes all Interest Payment Dates for the given payment context.
        """
        for i, pmt_cntx in enumerate(payment_contexts, 1):
            self.run_IPD(pmt_cntx, i)
