





    def allocate_principal(self, payment_context: PaymentContext) -> dict[str, float]:
        """
        Allocates principal payments based on the repayment structure of the deal.
        Returns a dictionary of principal allocations per tranche.
        """
        principal_allocations = PrincipalAllocationRules(self.deal.tranches, self.deal.repayment_structure).allocate_principal(payment_context)
        payment_context.principal_allocations = principal_allocations
        return principal_allocations
    
    def prep_IPD(self, payment_context: PaymentContext, period: int):
        """
        Wrapper of the PaymentContext dataclass - prepping states for run_IPD method
        """
        payment_context.last_period_liquidity_reserve_balance = self.deal.reserve.last_period_balance
        payment_context.available_revenue_collections = payment_context.revenue_collections + payment_context.last_period_liquidity_reserve_balance
        payment_context.available_redemption_collections = payment_context.redemption_collections

        payment_context.principal_allocations = self.allocate_principal(payment_context)
        payment_context.last_period_tranche_ending_balance_total = sum(t.last_period_ending_balance for t in self.deal.tranches)

        return payment_context