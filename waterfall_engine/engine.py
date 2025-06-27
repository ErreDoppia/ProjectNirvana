
from typing import TYPE_CHECKING


from .deal import Deal
from .models import WaterfallLimb
from .waterfalls import WaterfallCalculator
from .models import RawPaymentContext, RawPaymentContext, WaterfallLimbResult
from .context import PaymentContextPrepper


### RUN WATERFALL ENGINE ###
class WaterfallEngine:
    def __init__(self, deal: 'Deal'):
        """
        Orchestrator for running the waterfall logic on a given deal.
        """
        self.deal = deal

        self._prep_payment_context = PaymentContextPrepper(self.deal)

        self._waterfall_types = [key for key in self.deal.waterfalls]
        self._waterfall_calculators = {key: WaterfallCalculator(w) for key, w in self.deal.waterfalls.items()}

    def flush_waterfall(self, payment_context: 'RawPaymentContext', period: int, waterfall_type: str) -> dict[str, 'WaterfallLimbResult']:
        """
        Applies the revenue waterfall logic for a given payment context and period.
        Returns the results of the revenue distribution.
        """       
        return self._waterfall_calculators[waterfall_type].flush(payment_context, period, waterfall_type)
    
    def prep_context_for_IPD(self, raw_payment_context: 'RawPaymentContext', waterfall_type: str):
        """
        Updates payment context for the run_IPD method
        """
        prep_pmt_ctx = self._prep_payment_context.prep_payment_context_for_IPD(raw_payment_context, waterfall_type)
        return prep_pmt_ctx

    def run_IPD(self, payment_context: 'RawPaymentContext', period: int):
        """
        Executes one Interest Payment Date logic.
        """

        ## 1. Running Waterfalls
        results = {}
        for type in self._waterfall_types:
            prepped_payment_context = self.prep_context_for_IPD(payment_context, type)
            res = self.flush_waterfall(prepped_payment_context, period, type)
            results[type] = res


        rev_waterfall_results = results.get('revenue', 0.0)
        red_waterfall_results = results.get('redemption', 0.0)
        
        ## X. Update history
        # Update deal history with results
        self.update_deal_history(period, rev_waterfall_results, red_waterfall_results)

        # Update waterfall limbs history with 
        self.update_revenue_waterfall_limbs_history(period, rev_waterfall_results)
        self.update_redemption_waterfall_limbs_history(period, red_waterfall_results)

        # Update tranche internal states
        self.update_tranche_internal_states(rev_waterfall_results, red_waterfall_results)

        print(f"IPD number {period}")
        print(f"Interest: {self.deal.history_revenue[period-1]}")
        print("")
        print(f"Principal: {self.deal.history_redemption[period-1]}")
        print("")
        
    def run_all_IPDs(self, payment_contexts: list['RawPaymentContext']):
        """
        Executes all Interest Payment Dates for the given payment context.
        """
        for i, pmt_cntx in enumerate(payment_contexts, 1):
            self.run_IPD(pmt_cntx, i)




    def update_deal_history(
            self, period: int, revenue_results: dict[str, 'WaterfallLimbResult'], 
            redemption_results: dict[str, 'WaterfallLimbResult']
        ):
        """
        Updates the deal's history with the results of the revenue and redemption waterfalls.
        """
        snapshot_revenue = {period: revenue_results}
        snapshot_redemption = {period: redemption_results}

        self.deal.history_revenue.append(snapshot_revenue)
        self.deal.history_redemption.append(snapshot_redemption)

    def update_revenue_waterfall_limbs_history(self, period: int, revenue_results: dict[str, 'WaterfallLimbResult']):
        """
        Updates the relevant revenue waterfall limb history for the deal based on the revenue results.
        """
        for i, limb in enumerate(self.deal.revenue_waterfall_limbs.values(), start=1):
            if isinstance(limb, WaterfallLimb):
                limb_name = limb.name
                limb_key = f"{i} - {limb_name}"
                limb.update_history_revenue_distributions(
                    period=period,
                    due=revenue_results.get(limb_key, {}).get('amount_due', 0.0),
                    paid=revenue_results.get(limb_key, {}).get('amount_paid', 0.0),
                    unpaid=revenue_results.get(limb_key, {}).get('amount_unpaid', 0.0)
                )

    def update_tranches_last_period_interest(self, revenue_results: dict[str, 'WaterfallLimbResult']):
        """
        Updates each tranche's last paid and unpaid interest amounts based on the revenue waterfall results.
        """
        for i, tranche in enumerate(self.deal.tranches, start=1):
            limb_name = tranche.name
            limb_key = f"{i} - {limb_name}"
            tranche.update_last_paid_and_last_unpaid_interest(
                due=revenue_results.get(limb_key, {}).get('amount_due', 0.0),
                paid=revenue_results.get(limb_key, {}).get('amount_paid', 0.0),
                unpaid=revenue_results.get(limb_key, {}).get('amount_unpaid', 0.0)
            )

    def update_tranches_total_interest(self, revenue_results: dict[str, 'WaterfallLimbResult']):
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

    def update_redemption_waterfall_limbs_history(self, period: int, redemption_results: dict[str, 'WaterfallLimbResult']):
        """
        Updates the relevant redemption waterfall limb history for the deal based on the redemption results.
        """
        for i, limb in enumerate(self.deal.redemption_waterfall_limbs.values(), start=1):
            if isinstance(limb, WaterfallLimb):
                limb_name = limb.name
                limb_key = f"{i} - {limb_name}"
                limb.update_history_revenue_distributions(
                    period=period,
                    due=redemption_results.get(limb_key, {}).get('amount_due', 0.0),
                    paid=redemption_results.get(limb_key, {}).get('amount_paid', 0.0),
                    unpaid=redemption_results.get(limb_key, {}).get('amount_unpaid', 0.0)
                )
                
    def update_tranches_last_period_principal(self, redemption_results: dict[str, 'WaterfallLimbResult']):
        """
        Updates each tranche's last paid principal and balance based on the revenue waterfall results.
        """
        for i, tranche in enumerate(self.deal.tranches, start=1):
            limb_name = tranche.name
            limb_key = f"{i} - {limb_name}"
            tranche.update_last_period_principal(
                redemption_results.get(limb_key, {}).get('amount_paid', 0.0),
                redemption_results.get(limb_key, {}).get('amount_unpaid', 0.0))
        
    def update_tranche_internal_states(
        self, revenue_results: dict[str, 'WaterfallLimbResult'], 
        redemption_results: dict[str, 'WaterfallLimbResult']):
        """
        General method to update Tranche's internal states after payment run
        """
        self.update_tranches_last_period_interest(revenue_results)
        self.update_tranches_total_interest(revenue_results)
        self.update_tranches_last_period_principal(redemption_results)
