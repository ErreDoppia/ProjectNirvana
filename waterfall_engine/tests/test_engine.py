
import unittest
from waterfall_engine.engine import Deal, RunWaterfall
from waterfall_engine.tranche import Tranche
from waterfall_engine.fees import Fee  
from waterfall_engine.models import PaymentContext, RevenueProcessor, RedemptionProcessor
from waterfall_engine.waterfalls import RevenueWaterfall, RedemptionWaterfall


class TestDealInitialization(unittest.TestCase):
    """
    Unit test cases for the Deal class initialization and basic properties.
    Tests various configurations of tranches, fees, and waterfalls.
    """

    def setUp(self):
        """
        Set up Deal instances for different test scenarios.
        """
        tranche_a = Tranche("A", 100e6, 0, 1.1/100, 60, "Q")
        tranche_b = Tranche("B", 50e6, 0, 2/100, 60, "Q")

        issuer_profit = Fee(name="issuer_profit", fee_config={"type": "dollar_amount", "amount": 250.0}, payment_frequency="Q")
        servicer_fee = Fee("servicer", {"type": "percentage", "amount": 0.01}, "Q", True)

        revenue_waterfall_limbs = {
            1: issuer_profit,
            2: servicer_fee, 
            3: RevenueProcessor(tranche_a),
            4: RevenueProcessor(tranche_b),
        }
            
        redemption_waterfall_limbs = {
            1: RedemptionProcessor(tranche_a),
            2: RedemptionProcessor(tranche_b),
        }

        self.my_deal = Deal(
            name="RR25-1",
            tranches=[tranche_a, tranche_b],
            fees=[issuer_profit, servicer_fee],
            repayment_structure="pro-rata",
            revenue_waterfall_limbs=revenue_waterfall_limbs, 
            redemption_waterfall_limbs=redemption_waterfall_limbs,
        )
        
    def test_initialization(self):
        """
        Test that the Deal initializes correctly with given parameters.
        """
        self.assertEqual(self.my_deal.name, "RR25-1")
        self.assertEqual(len(self.my_deal.tranches), 2)

    def test_revenue_waterfall(self):
        """
        Test the revenue waterfall calculations.
        """

        payment_context = [PaymentContext(
            available_revenue_collections=1000000,
            available_redemption_collections=0,
            pool_balance=150e6,
            principal_allocations={"A": 5e6, "B": 5e6}
        ) for _ in range(10)]  # Simulating 10 quarters of payments

        RunWaterfall(self.my_deal).run_all_IPDs(payment_context)
        
        results = self.my_deal.history_revenue
        self.assertGreater(len(results), 0, "Revenue waterfall should have results after running IPDs")
        self.assertIsInstance(results[0], dict, "Each result should be a dictionary of results")    

        for result in results:
            for period, data in result.items():
                self.assertAlmostEqual(data['1 - issuer_profit']['amount_paid'], 250.0)
                self.assertAlmostEqual(data['2 - servicer']['amount_paid'], 375000.0)
                self.assertAlmostEqual(data['3 - A']['amount_paid'], 100e6 * 1.1/100 /4)
                self.assertAlmostEqual(data['4 - B']['amount_paid'], 50e6 * 2/100 /4)
                self.assertAlmostEqual(data['excess_spread']['amount_paid'], 99750.0)

    def test_pro_rata_redemption_waterfall(self):
        """
        Test the redemption waterfall calculations.
        """

        payment_context = [PaymentContext(
            available_revenue_collections=0,
            available_redemption_collections=1.5e6,
            pool_balance=150e6,
            principal_allocations={"A": 1e6, "B": 0.5e6}
        ) for _ in range(10)]

        RunWaterfall(self.my_deal).run_all_IPDs(payment_context)

        results = self.my_deal.history_redemption
        self.assertGreater(len(results), 0, "Redemption waterfall should have results after running IPDs")
        self.assertIsInstance(results[0], dict, "Each result should be a dictionary of results")

        for result in results:
            for period, data in result.items():
                self.assertAlmostEqual(
                    data['1 - A']['amount_paid'], 1e6,
                    msg=f"Period {period} - Error in A tranche redemption: {data['1 - A']['amount_paid']}"
                )
                self.assertAlmostEqual(
                    data['2 - B']['amount_paid'], 0.5e6,
                    msg=f"Period {period} - Error in B tranche redemption: {data['2 - B']['amount_paid']}"
                )
                self.assertAlmostEqual(
                    data['excess_spread']['amount_paid'], 0.0,
                    msg=f"Period {period} - Error in excess spread redemption: {data['excess_spread']['amount_paid']}"
                )

    def test_sequential_redemption_waterfall(self):
        """
        Test the redemption waterfall with sequential allocation.
        """

        self.my_deal.repayment_structure = "sequential"

        payment_context = [PaymentContext(
            available_revenue_collections=0,
            available_redemption_collections=1.5e6,
            pool_balance=150e6,
            principal_allocations={"A": 1.5e6, "B": 0.0}
        ) for _ in range(10)]

        RunWaterfall(self.my_deal).run_all_IPDs(payment_context)

        results = self.my_deal.history_redemption
        self.assertGreater(len(results), 0, "Redemption waterfall should have results after running IPDs")
        self.assertIsInstance(results[0], dict, "Each result should be a dictionary of results")

        for result in results:
            for period, data in result.items():
                self.assertAlmostEqual(
                    data['1 - A']['amount_paid'], 1.5e6,
                    msg=f"Period {period} - Error in A tranche redemption: {data['1 - A']['amount_paid']}"
                )
                self.assertAlmostEqual(
                    data['2 - B']['amount_paid'], 0.0,
                    msg=f"Period {period} - Error in B tranche redemption: {data['2 - B']['amount_paid']}"
                )
                self.assertAlmostEqual(
                    data['excess_spread']['amount_paid'], 0.0,
                    msg=f"Period {period} - Error in excess spread redemption: {data['excess_spread']['amount_paid']}"
                )
