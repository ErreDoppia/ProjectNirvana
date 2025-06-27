

import unittest
from waterfall_engine.fees import Fee
from waterfall_engine.models import RawPaymentContext, PaymentContext
from waterfall_engine.context import PaymentContextPrepper


class TestFeeAmountsDue(unittest.TestCase):
    """
    Unit test cases for the Fee class amount due calculations.
    Tests various fee configurations and validates correct due amounts.
    """
    def setUp(self):
        """
        Set up Fee instances for different test scenarios.
        """
        self.fee_dollar_amount_periodical = Fee(
            name="TestFeeDollarAmountAnnual",
            fee_config={
                'type': 'dollar_amount',
                'amount': 1000.0
            },
            payment_frequency='Q',
            annual=False,
            payment_periods=None
        )

        self.fee_dollar_amount_annual = Fee(
            name="TestFeeDollarAmountAnnual",
            fee_config={
                'type': 'dollar_amount',
                'amount': 1000.0
            },
            payment_frequency='Q',
            annual=True,
            payment_periods=None
        )

        self.fee_percentage = Fee(
            name="TestFeePercentage",
            fee_config={
                'type': 'percentage',
                'amount': 0.05  # 5%
            },
            payment_frequency='Q',
            annual=False,
            payment_periods=None,
        )

    def test_fee_dollar_amount_periodical_due(self):
        """
        Test that a periodical dollar amount fee returns the correct due amount.
        """
        pool_balance = 10e6
        period = 1
        expected_due = 1000.0
        actual_due = self.fee_dollar_amount_periodical.amount_due(pool_balance, period)
        self.assertEqual(actual_due, expected_due, msg="Dollar amount fee due calculation is incorrect.")

    def test_fee_percentage_due(self):
        """
        Test that a percentage-based fee returns the correct due amount.
        """
        pool_balance = 10e6
        period = 1
        expected_due = 0.5e6  # 5% of 10 million
        actual_due = self.fee_percentage.amount_due(pool_balance, period)
        self.assertEqual(actual_due, expected_due, msg="Percentage fee due calculation is incorrect.")

    def test_fee_dollar_amount_annual_due(self):
        """
        Test that an annual dollar amount fee is correctly divided by frequency multiplier.
        """
        pool_balance = 10e6
        period = 1
        expected_due = 250.0 # 1000 / 4 (quarterly payment)
        actual_due = self.fee_dollar_amount_annual.amount_due(pool_balance, period)
        self.assertEqual(actual_due, expected_due, msg="Annual dollar amount fee due calculation is incorrect.")

    def test_fee_not_due_in_non_payment_period(self):
        """
        Test that the fee is not due in periods not listed in payment_periods.
        """
        fee = Fee(
            name="TestFee",
            fee_config={'type': 'dollar_amount', 'amount': 1000.0},
            payment_frequency='Q',
            annual=False,
            payment_periods=[1, 3]  # Only due in periods 1 and 3
        )
        pool_balance = 10e6
        period = 2
        expected_due = 0.0
        actual_due = fee.amount_due(pool_balance, period)
        self.assertEqual(actual_due, expected_due, msg="Fee should not be due in non-payment period.")

    def test_invalid_fee_config(self):
        """
        Test that an invalid fee configuration raises a ValueError.
        """
        with self.assertRaises(ValueError, msg="Invalid fee config should raise ValueError."):
            Fee(
                name="InvalidFee",
                fee_config={'type': 'invalid_type', 'amount': 1000.0},
                payment_frequency='Q',
                annual=False
            )

    def test_invalid_payment_frequency(self):
        """
        Test that an invalid payment frequency raises a ValueError.
        """
        with self.assertRaises(ValueError, msg="Invalid payment frequency should raise ValueError."):
            Fee(
                name="InvalidFee",
                fee_config={'type': 'dollar_amount', 'amount': 1000.0},
                payment_frequency='X',
                annual=False
            )


class TestFeeDistribution(unittest.TestCase):
    """
    Unit test cases for the Fee class distribution logic.
    Tests the distribution of payments and history tracking.
    """
    def setUp(self):
        """
        Set up a Fee instance for distribution tests.
        """
        self.fee = Fee(
            name="TestFee",
            fee_config={'type': 'dollar_amount', 'amount': 1000.0},
            payment_frequency='Q',
            annual=False,
            payment_periods=None
        )

    def test_fee_distribution(self):
        """
        Test the distribution of fee payments over multiple periods and verify history.
        """
        raw_pmt_ctx = [RawPaymentContext(revenue_collections=10000.0, redemption_collections=0.0,pool_balance=10e6),
                       RawPaymentContext(revenue_collections=500.0, redemption_collections=0.0,pool_balance=10e6),
                       RawPaymentContext(revenue_collections=10000.0, redemption_collections=0.0,pool_balance=10e6)]

        payment_context = [
            PaymentContext(raw_payment_context=raw_pmt_ctx[0], available_cash=10000, last_period_liquidity_reserve_balance=0.0, 
                           last_period_tranche_ending_balance_total=0.0),
            PaymentContext(raw_payment_context=raw_pmt_ctx[1], available_cash=500, last_period_liquidity_reserve_balance=0.0, 
                           last_period_tranche_ending_balance_total=0.0),
            PaymentContext(raw_payment_context=raw_pmt_ctx[2], available_cash=10000, last_period_liquidity_reserve_balance=0.0, 
                           last_period_tranche_ending_balance_total=0.0)
        ]
        


        expected_history = []

        # Simulate fee distribution for each period and build expected history
        for i, context in enumerate(payment_context, start=1):
            self.fee.apply_amount_due(context, i, 'revenue')

            due = 1e3
            paid = min(context.revenue_collections, due)
            unpaid = due - paid

            expected_history.append({
                'period': i,
                'amount_due': due,
                'amount_paid': paid,
                'amount_unpaid': unpaid                
            })

        result = self.fee.history

        # Compare each period's history entry with expected values
        for exp, res in zip(expected_history, result):
            for key in exp:
                self.assertEqual(exp[key], res[key], 
                                 msg=f"Mismatch in {key} for period {exp['period']}.")
                
    def test_fee_distribution_with_no_funds(self):
        """
        Test fee distribution when no funds are available.
        """
        payment_context = PaymentContext(
            RawPaymentContext(pool_balance=10e6, revenue_collections=0.0, redemption_collections=0.0), 
            available_cash=0.0, last_period_liquidity_reserve_balance=0.0, last_period_tranche_ending_balance_total=0.0)
        period = 1

        result = self.fee.apply_amount_due(payment_context, period, 'revenue')

        expected_result = {
            'amount_due': 1000.0,
            'amount_paid': 0.0,
            'amount_unpaid': 1000.0
        }

        self.assertEqual(result, expected_result, 
                         msg="Fee distribution with no funds should return zero distributed and full unpaid amount.")
        
    def test_fee_with_payment_periods(self):
        """
        Test fee distribution with specific payment periods.
        """
        fee = Fee(
            name="TestFeeWithPeriods",
            fee_config={'type': 'dollar_amount', 'amount': 1000.0},
            payment_frequency='Q',
            annual=False,
            payment_periods=[1, 3]  # Only due in periods 1 and 3
        )

        payment_context = PaymentContext(
            RawPaymentContext(pool_balance=10e6, revenue_collections=10000.0, redemption_collections=0.0), 
            available_cash=10e3, last_period_liquidity_reserve_balance=0.0, last_period_tranche_ending_balance_total=0.0)

        # Period 1 should distribute
        result_period_1 = fee.apply_amount_due(payment_context, 1, 'revenue')
        self.assertEqual(result_period_1['amount_paid'], 1000.0)
        self.assertEqual(result_period_1['amount_unpaid'], 0.0)

        # Period 2 should not distribute
        result_period_2 = fee.apply_amount_due(payment_context, 2, 'revenue')
        self.assertEqual(result_period_2['amount_paid'], 0.0)
        self.assertEqual(result_period_2['amount_unpaid'], 0.0)

        # Period 3 should distribute
        result_period_3 = fee.apply_amount_due(payment_context, 3, 'revenue')
        self.assertEqual(result_period_3['amount_paid'], 1000.0)
        self.assertEqual(result_period_3['amount_unpaid'], 0.0)

if __name__ == '__main__':
    unittest.main()


