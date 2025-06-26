
from .deal import Deal
from .models import RawPaymentContext, PaymentContext
from .calculations import PrincipalAllocationRules

class PaymentContextPrepper:
    def __init__(self, deal: Deal) -> None:
        self.deal = deal

        # internal flag
        self._prepped = False

    def prep_payment_context(self, raw_payment_context: RawPaymentContext) -> PaymentContext:

        last_period_liquidity_reserve_balance = self.deal.reserve.last_period_balance

        if self.deal.reserve is not None:
            available_revenue_collections = raw_payment_context.revenue_collections + self.deal.reserve.last_period_balance
        else:
            available_revenue_collections = raw_payment_context.revenue_collections
        
        available_redemption_collections = raw_payment_context.redemption_collections
        
        last_period_tranche_ending_balance_total = sum(t.last_period_ending_balance for t in self.deal.tranches)

        context = PaymentContext(
            payment_context=raw_payment_context,
            available_revenue_collections=available_revenue_collections,
            available_redemption_collections=available_redemption_collections,
            last_period_tranche_ending_balance_total=last_period_tranche_ending_balance_total,
            last_period_liquidity_reserve_balance=last_period_liquidity_reserve_balance,
        )

        self._prepped = True

        self.allocate_principal(context)

        return context
     
    def allocate_principal(self, payment_context: PaymentContext) -> dict[str, float]:
        """
        Allocates principal payments based on the repayment structure of the deal.
        Returns a dictionary of principal allocations per tranche.
        """
        if not self._prepped:
            raise RuntimeError("Allocate principal can be called after prep_payment_context method")
        allocations = PrincipalAllocationRules(self.deal.tranches, self.deal.repayment_structure).allocate_principal(payment_context)
        payment_context.principal_allocations = allocations
        return allocations