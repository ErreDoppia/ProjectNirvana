
from .tranche import Tranche
from .models import RedemptionWaterfallLimb, RevenueWaterfallLimb, WaterfallLimbResult
from .utils import get_limb_key


class History:        
    @staticmethod
    def update_revenue_waterfall_limbs_history(
        limbs: list[RevenueWaterfallLimb], period: int, 
        revenue_results: dict[str, WaterfallLimbResult]):
        """
        Updates the relevant revenue waterfall limb history for the deal based on the revenue results.
        """
        for i,limb in enumerate(limbs, start=1):
            limb_key = get_limb_key(i, limb.name)

            limb.update_history_revenue_distributions(
                period=period,
                due=revenue_results.get(limb_key, {}).get('amount_due', 0.0),
                paid=revenue_results.get(limb_key, {}).get('amount_paid', 0.0),
                unpaid=revenue_results.get(limb_key, {}).get('amount_unpaid', 0.0)
            )

    @staticmethod
    def update_tranches_last_period_interest(
        tranches: list[Tranche],
        revenue_results: dict[str, WaterfallLimbResult]):
        """
        Updates each tranche's last paid and unpaid interest amounts based on the revenue waterfall results.
        """
        for i, tranche in enumerate(tranches, start=1):
            limb_key = get_limb_key(i, tranche.name)
            tranche.update_last_paid_and_last_unpaid_interest(
                paid=revenue_results.get(limb_key, {}).get('amount_paid', 0.0),
                unpaid=revenue_results.get(limb_key, {}).get('amount_unpaid', 0.0)
            )

    @staticmethod
    def update_tranches_total_interest(
        tranches: list[Tranche],
        revenue_results: dict[str, WaterfallLimbResult]):
        """
        Updates each tranche's total paid and unpaid interest amounts based on the revenue waterfall results.
        """
        for i, tranche in enumerate(tranches, start=1):
            if isinstance(tranche, Tranche):
                limb_key = get_limb_key(i, tranche.name)
                tranche.update_total_paid_and_total_unpaid_interest(
                    paid=revenue_results.get(limb_key, {}).get('amount_paid', 0.0),
                    unpaid=revenue_results.get(limb_key, {}).get('amount_unpaid', 0.0)
                )

    @staticmethod
    def update_redemption_waterfall_limbs_history(
        limbs: list[RevenueWaterfallLimb], period: int, 
        redemption_results: dict[str, WaterfallLimbResult]):
        """
        Updates the relevant redemption waterfall limb history for the deal based on the redemption results.
        """
        for i, limb in enumerate(limbs, start=1):
            limb_key = get_limb_key(i, limb.name)
            limb.update_history_revenue_distributions(
                period=period,
                due=redemption_results.get(limb_key, {}).get('amount_due', 0.0),
                paid=redemption_results.get(limb_key, {}).get('amount_paid', 0.0),
                unpaid=redemption_results.get(limb_key, {}).get('amount_unpaid', 0.0)
            )

    @staticmethod   
    def update_tranches_last_period_principal(
        tranches: list[Tranche], redemption_results: dict[str, WaterfallLimbResult]):
        """
        Updates each tranche's last paid principal and balance based on the revenue waterfall results.
        """
        for i, tranche in enumerate(tranches, start=1):
            limb_name = tranche.name
            limb_key = f"{i} - {limb_name}"
            tranche.update_last_period_paid_principal(redemption_results.get(limb_key, {}).get('amount_paid', 0.0))
            tranche.update_last_period_ending_balance(redemption_results.get(limb_key, {}).get('amount_unpaid', 0.0))
        