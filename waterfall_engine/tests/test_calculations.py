

import unittest

from waterfall_engine.calculations import PrincipalAllocationRules
from waterfall_engine.models import RawPaymentContext, WaterfallProcessor, PaymentContext
from waterfall_engine.tranche import Tranche
from waterfall_engine.deal import Deal
from waterfall_engine.reserve import NonLiquidityReserve


class TestPrincipalAllocationRules(unittest.TestCase):
    def setUp(self):
        """
        Set up a Deal instance for testing.
        """
        self.tranche_a = Tranche("A", 100e6, 0, 1.1/100, 60, "Q")
        self.tranche_b = Tranche("B", 50e6, 0, 2/100, 60, "Q")

        redemption_waterfall_limbs = {
            1: WaterfallProcessor(self.tranche_a),
            2: WaterfallProcessor(self.tranche_b),
        }

        self.my_deal = Deal(
            name="RR25-1",
            fees=[],
            tranches=[self.tranche_a, self.tranche_b],
            reserve=NonLiquidityReserve('non_liquidity_reserve', 0.0, 0, 'pool_balance'),
            repayment_structure="sequential",
            waterfalls={'redemption': redemption_waterfall_limbs},
        )

    def test_allocate_principal_sequential(self):
        """
        Test principal allocation in sequential mode.
        """
        payment_context = PaymentContext(
            RawPaymentContext(redemption_collections=1.5e6, revenue_collections=0, pool_balance=150e6), 
            available_cash=1.5e6, last_period_liquidity_reserve_balance=-0.0, last_period_tranche_ending_balance_total=0.0)

        allocation = PrincipalAllocationRules(self.my_deal.tranches, self.my_deal.repayment_structure).allocate_principal(payment_context)

        expected_allocation = {
            "A": 1.5e6,
            "B": 0.0
        }
        
        self.assertEqual(allocation, expected_allocation)

    def test_allocate_principal_pro_rata(self):
        """
        Test principal allocation in pro-rata mode.
        """
        self.my_deal.repayment_structure = "pro-rata"
        payment_context = PaymentContext(
            RawPaymentContext(redemption_collections=1.5e6, revenue_collections=0, pool_balance=150e6), 
            available_cash= 1.5e6,
            last_period_liquidity_reserve_balance=0.0,
            last_period_tranche_ending_balance_total=0.0 
        )

        allocation = PrincipalAllocationRules(self.my_deal.tranches, self.my_deal.repayment_structure).allocate_principal(payment_context)

        expected_allocation = {
            "A": 1.0e6,
            "B": 0.5e6
        }
        
        self.assertEqual(allocation, expected_allocation)

