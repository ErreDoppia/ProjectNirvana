

import unittest

from waterfall_engine.calculations import PrincipalAllocationRules
from waterfall_engine.models import PaymentContext
from waterfall_engine.tranche import Tranche, RevenueProcessor, RedemptionProcessor
from waterfall_engine.deal import Deal


class TestPrincipalAllocationRules(unittest.TestCase):
    def setUp(self):
        """
        Set up a Deal instance for testing.
        """
        self.tranche_a = Tranche("A", 100e6, 0, 1.1/100, 60, "Q")
        self.tranche_b = Tranche("B", 50e6, 0, 2/100, 60, "Q")

        self.redemption_waterfall_limbs = {
            1: RedemptionProcessor(self.tranche_a),
            2: RedemptionProcessor(self.tranche_b),
        }

        self.my_deal = Deal(
            name="RR25-1",
            fees=[],
            revenue_waterfall_limbs={},
            tranches=[self.tranche_a, self.tranche_b],
            repayment_structure="sequential",
            redemption_waterfall_limbs=self.redemption_waterfall_limbs,
        )

    def test_allocate_principal_sequential(self):
        """
        Test principal allocation in sequential mode.
        """
        payment_context = PaymentContext(available_redemption_collections=1.5e6, available_revenue_collections=0, pool_balance=150e6)
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
        payment_context = PaymentContext(available_redemption_collections=1.5e6, available_revenue_collections=0, pool_balance=150e6)
        allocation = PrincipalAllocationRules(self.my_deal.tranches, self.my_deal.repayment_structure).allocate_principal(payment_context)

        expected_allocation = {
            "A": 1.0e6,
            "B": 0.5e6
        }
        
        self.assertEqual(allocation, expected_allocation)

