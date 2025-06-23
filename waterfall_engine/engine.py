
from typing import Optional
from abc import ABC, abstractmethod
from typing import TypedDict

from .settings import FREQ_MULTIPLIER
from .tranche import Tranche
from .fees import Fee
from .deal import Deal
from .models import RevenueWaterfallLimb, RedemptionWaterfallLimb
from .waterfalls import RevenueWaterfall, RedemptionWaterfall
from .models import ApplyRevenueDueResult, ApplyRedemptionDueResult
from .models import PaymentContext, WaterfallLimbResult
from .calculations import PrincipalAllocationRules   


### RUN WATERFALL ENGINE ###
class RunWaterfall:
    def __init__(self, deal: Deal):
        """
        Orchestrator for running the waterfall logic on a given deal.
        """
        self.deal = deal

        self._revenue_waterfall = RevenueWaterfall(self.deal.revenue_waterfall_limbs)
        self._redemption_waterfall = RedemptionWaterfall(self.deal.redemption_waterfall_limbs)

    def apply_revenue_waterfall(self, payment_context: PaymentContext, period: int) -> dict[str, WaterfallLimbResult]:
        """
        Applies the revenue waterfall logic for a given payment context and period.
        Returns the results of the revenue distribution.
        """
        return self._revenue_waterfall.apply(payment_context, period)

    def apply_redemption_waterfall(self, payment_context: PaymentContext, period: int) -> dict[str, WaterfallLimbResult]:
        """
        Applies the redemption waterfall logic for a given payment context and period.
        Returns the results of the redemption distribution.
        """
        return self._redemption_waterfall.apply(payment_context, period)

    def update_deal_history(
            self, period: int, revenue_results: dict[str, WaterfallLimbResult], 
            redemption_results: dict[str, WaterfallLimbResult]
        ):
        """
        Updates the deal's history with the results of the revenue and redemption waterfalls.
        """
        snapshot_revenue = {period: revenue_results}
        snapshot_redemption = {period: redemption_results}

        self.deal.history_revenue.append(snapshot_revenue)
        self.deal.history_redemption.append(snapshot_redemption)

    def update_revenue_waterfall_limbs_history(self, period: int, revenue_results: dict[str, WaterfallLimbResult]):
        """
        Updates the relevant waterfall limb history for the deal based on the revenue results.
        """
        for i, limb in enumerate(self.deal.revenue_waterfall_limbs.values(), start=1):
            if isinstance(limb, RevenueWaterfallLimb):
                limb_name = limb.name
                limb_key = f"{i} - {limb_name}"
                limb.update_history_revenue_distributions(
                    period=period,
                    due=revenue_results.get(limb_key, {}).get('amount_due', 0.0),
                    paid=revenue_results.get(limb_key, {}).get('amount_paid', 0.0),
                    unpaid=revenue_results.get(limb_key, {}).get('amount_unpaid', 0.0)
                )

    def update_tranches_last_period_interest(self, period, revenue_results: dict[str, WaterfallLimbResult]):
        """
        Updates each tranche's last paid and unpaid interest amounts based on the revenue waterfall results.
        """
        for i, tranche in enumerate(self.deal.tranches, start=1):
            limb_name = tranche.name
            limb_key = f"{i} - {limb_name}"
            tranche.update_last_paid_and_last_unpaid_interest(
                paid=revenue_results.get(limb_key, {}).get('amount_paid', 0.0),
                unpaid=revenue_results.get(limb_key, {}).get('amount_unpaid', 0.0)
            )

    def update_tranches_total_interest(self, period, revenue_results: dict[str, WaterfallLimbResult]):
        """
        Updates each tranche's total paid and unpaid interest amounts based on the revenue waterfall results.
        """
        for i, tranche in enumerate(self.deal.tranches, start=1):
            limb_name = tranche.name
            limb_key = f"{i} - {limb_name}"
            tranche.update_total_paid_and_total_unpaid_interest(
                paid=revenue_results.get(limb_key, {}).get('amount_paid', 0.0),
                unpaid=revenue_results.get(limb_key, {}).get('amount_unpaid', 0.0)
            )


    def allocate_principal(self, payment_context: PaymentContext) -> dict[str, float]:
        """
        Allocates principal payments based on the repayment structure of the deal.
        Returns a dictionary of principal allocations per tranche.
        """
        principal_allocations = PrincipalAllocationRules(self.deal.tranches, self.deal.repayment_structure).allocate_principal(payment_context)
        payment_context.principal_allocations = principal_allocations
        return principal_allocations

    def run_IPD(self, payment_context: PaymentContext, period: int):
        """
        Executes one Interest Payment Date logic.
        """
        principal_allocations = self.allocate_principal(payment_context)

        if payment_context.principal_allocations == principal_allocations:
            # Apply revenue and redemption waterfalls
            rev_waterfall_results = self.apply_revenue_waterfall(payment_context, period)
            red_waterfall_results = self.apply_redemption_waterfall(payment_context, period)
        else:
            raise ValueError("Principal allocations do not match expected allocations.")
        
        # Update deal history with results
        self.update_deal_history(period, rev_waterfall_results, red_waterfall_results)
        self.update_revenue_waterfall_limbs_history(period, rev_waterfall_results)
        self.update_tranches_last_period_interest(period, rev_waterfall_results)

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
