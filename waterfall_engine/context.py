
from .deal import Deal
from .models import RawPaymentContext, PaymentContext
from .calculations import PrincipalAllocationRules


class PaymentContextPrepper:
    def __init__(self, deal: Deal) -> None:
        self.deal = deal

        # internal flag
        self._prepped = False

    def prep_payment_context_for_IPD(self, raw_payment_context: RawPaymentContext, waterfall_type: str) -> RawPaymentContext:

        last_period_liquidity_reserve_balance = self.deal.reserve.last_period_balance

        last_period_tranche_ending_balance_total = sum(t.last_period_ending_balance for t in self.deal.tranches)

        if waterfall_type=="revenue":
            if self.deal.reserve is not None:
                available_cash = raw_payment_context.revenue_collections + self.deal.reserve.last_period_balance
            else:
                available_cash = raw_payment_context.revenue_collections

        elif waterfall_type=="redemption":
            available_cash = raw_payment_context.redemption_collections

        else:
            raise ValueError(f"Invalid waterfall_type:  {waterfall_type}")
        
        context = PaymentContext(
            raw_payment_context=raw_payment_context,
            last_period_tranche_ending_balance_total=last_period_tranche_ending_balance_total,
            last_period_liquidity_reserve_balance=last_period_liquidity_reserve_balance,
            available_cash=available_cash
        )

        self._prepped = True

        self._allocate_principal(context)

        return context
     
    def _allocate_principal(self, payment_context: PaymentContext) -> dict[str, float]:
        """
        Allocates principal payments based on the repayment structure of the deal.
        Returns a dictionary of principal allocations per tranche.
        """
        if not self._prepped:
            raise RuntimeError("Allocate principal can be called after prep_payment_context method")
        allocations = PrincipalAllocationRules(self.deal.tranches, self.deal.repayment_structure).allocate_principal(payment_context)
        payment_context.principal_allocations = allocations
        return allocations
    

class PaymentContextHandler:
    @staticmethod
    def reduce_available_cash_in_place(payment_context: RawPaymentContext, cash_distributed: float, waterfall_type: str) -> None:
        """
        """
        payment_context.available_cash -= cash_distributed 