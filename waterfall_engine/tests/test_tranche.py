
import unittest
from waterfall_engine.tranche import Tranche
from waterfall_engine.models import PaymentContext, RedemptionProcessor


class TestInterestCalcs(unittest.TestCase):
    """
    Unit tests for interest-related methods in the Tranche class.
    """
    def setUp(self):
        """Set up a standard tranche instance for testing."""
        self.tranche = Tranche(
            name='test_tranche', 
            initial_balance=100e6, 
            reference_rate=0.02, 
            margin=0.06, 
            maturity=60, 
            payment_frequency='Q', 
            step_up_margin=0.1,
            step_up_date=36)

    def test_no_step_up_margin(self):
        """Test margin before the step-up date (uses base margin)."""
        result = self.tranche.current_period_margin(period=35)
        expected = 0.06
        self.assertAlmostEqual(result, expected)

    def test_step_up_margin(self):
        """Test margin after the step-up date (uses step-up margin)."""
        result = self.tranche.current_period_margin(period=36)
        expected = 0.1
        self.assertAlmostEqual(result, expected)

    def test_current_all_in_rate_no_margin(self):
        """Test all-in rate before step-up (reference rate + base margin)."""
        result = self.tranche.current_all_in_rate(period=35)
        expected = 0.02 + 0.06
        self.assertAlmostEqual(result, expected)

    def test_interest_due(self):
        """Test calculation of interest due in a period without arrears."""
        result = self.tranche.current_interest_due(period=1)
        expected = round(100e6 * (0.02 + 0.06) / 4, 2)
        self.assertAlmostEqual(result, expected)

    def test_update_last_period_paid_and_unpaid_interest(self):
        paid = 10e3
        unpaid = 0
        self.tranche.update_last_paid_and_last_unpaid_interest(paid, unpaid)

        result1 = self.tranche.last_period_paid_interest
        result2 = self.tranche.last_period_unpaid_interest

        self.assertAlmostEqual(paid, result1)
        self.assertAlmostEqual(unpaid, result2)

    def test_write_off_unpaid_interest(self):
        temp_tranche = Tranche(
                name='test_tranche', 
                initial_balance=100e6, 
                reference_rate=0.02, 
                margin=0.06, 
                maturity=60, 
                payment_frequency='Q', 
                step_up_margin=0.1,
                step_up_date=36,
                write_off_unpaid_interest=True
            )
        
        temp_tranche.update_total_paid_and_total_unpaid_interest(10e3, 10e3)
        result = temp_tranche.last_period_paid_interest

        self.assertAlmostEqual(temp_tranche.total_paid_interest,10e3)
        self.assertAlmostEqual(temp_tranche.total_unpaid_interest,10e3)
        self.assertAlmostEqual(result,0)

    def test_current_interest_accrued_on_arrears(self):
        """Test interest accrued on unpaid interest (arrears) from previous period."""
        self.tranche.update_last_paid_and_last_unpaid_interest(1.5e6, 0.5e6)
        result = self.tranche.current_interest_on_last_period_unpaid_interest(1)
        expected = round(500e3 * (0.02 + 0.06) / 4, 2)
        self.assertAlmostEqual(result, expected)

    def test_current_total_interest_due(self):
        """
        Test total interest due: current interest + prior arrears + 
        interest on arrears (no step-up).
        """
        self.tranche.update_last_paid_and_last_unpaid_interest(1.5e6, 0.5e6)
        result = self.tranche.current_total_interest_due(1)

        current_interest_due = round(100e6 * (0.02 + 0.06) / 4, 2)
        last_period_unpaid = 0.5e6
        interest_on_last_period_unpaid = round(0.5e6 * (0.02 + 0.06) / 4, 2)
        expected = current_interest_due + last_period_unpaid + interest_on_last_period_unpaid

        self.assertAlmostEqual(result, expected)

    def test_current_total_interest_due_step_up(self):
        """
        Test total interest due including step-up margin (after step-up date).
        """
        self.tranche.update_last_paid_and_last_unpaid_interest(1.5e6, 0.5e6)
        result = self.tranche.current_total_interest_due(36)

        current_interest_due = round(100e6 * (0.02 + 0.1) / 4, 2)
        last_period_unpaid = 0.5e6
        interest_on_last_period_unpaid = round(0.5e6 * (0.02 + 0.1) / 4, 2)
        expected = current_interest_due + last_period_unpaid + interest_on_last_period_unpaid
        self.assertAlmostEqual(result, expected)

    def test_invalid_payment_frequency(self):
        """Test that an invalid payment frequency raises a ValueError."""
        with self.assertRaises(ValueError):
            Tranche(
                name='test_tranche', 
                initial_balance=100e6, 
                reference_rate=0.02, 
                margin=0.06, 
                maturity=60, 
                payment_frequency='XYZ',  # Invalid frequency
                step_up_margin=0.1,
                step_up_date=36
            )


class TestPrincipalCalcs(unittest.TestCase):
    """
    Unit tests for principal tracking and balance updates in the Tranche class.
    """
    def setUp(self):
        """Create a fresh tranche instance for balance tracking tests."""
        self.tranche = Tranche(
            name='test_tranche', 
            initial_balance=100e6, 
            reference_rate=0.02, 
            margin=0.06, 
            maturity=60, 
            payment_frequency='Q', 
            step_up_margin=0.1,
            step_up_date=36)

    def test_balance_update(self):
        """Test that ending balance updates correctly after payment."""
        result1 = self.tranche.last_period_ending_balance
        expected1 = 100e6
        self.assertAlmostEqual(result1, expected1)

        # Simulate a principal repayment of 10M
        self.tranche.update_last_period_ending_balance(90e6)

        result2 = self.tranche.last_period_ending_balance
        expected2 = 90e6
        self.assertAlmostEqual(result2, expected2)


class TestTrancheIntegration(unittest.TestCase):
    """
    Integration tests for for waterfall runs
    """
    def setUp(self):
        """Create a fresh tranche instance for balance tracking tests."""
        self.tranche = Tranche(
            name='test_tranche', 
            initial_balance=10e6, 
            reference_rate=0.02, 
            margin=0.06, 
            maturity=60, 
            payment_frequency='Q', 
            step_up_margin=0.1,
            step_up_date=36
        )

    def test_repayment_runs(self):
        """
        Tests that multiple periods of principal repayments are correctly processed
        and tracked in the tranche's principal repayment history.
        """
        
        # Simulated payment context for 3 periods
        payment_context = [
            PaymentContext(available_redemption_collections=5e6, available_revenue_collections=0.0, pool_balance=10e6, principal_allocations={"test_tranche": 5e6}, revenue_collections=0.0, redemption_collections=0.0,),
            PaymentContext(available_redemption_collections=2.5e6, available_revenue_collections=0.0, pool_balance=10e6, principal_allocations={"test_tranche": 2.5e6}, revenue_collections=0.0, redemption_collections=0.0,),
            PaymentContext(available_redemption_collections=2.5e6, available_revenue_collections=0.0, pool_balance=10e6, principal_allocations={"test_tranche": 2.5e6}, revenue_collections=0.0, redemption_collections=0.0,)
        ]
        
        initial_balance = 10e6
        expected = []

        # Loop through each period's payment context
        for i, pmt_cntx in enumerate(payment_context, 1):
            # Run the redemption process for the period

            payment_run = self.tranche.apply_redemption_due(pmt_cntx, i)
            paid = payment_run.get('redemption_funds_distributed')
            unpaid = payment_run.get('redemption_amount_unpaid')
            self.tranche.update_history_redemption_distributions(i, paid, unpaid)
            self.tranche.update_last_period_ending_balance(unpaid)

            # Construct expected output for the history
            exp_history = {
                'period': i,
                'last_period_ending_balance': initial_balance,
                'current_period_repayments': pmt_cntx.available_redemption_collections,
                'current_period_ending_balance': initial_balance - pmt_cntx.available_redemption_collections
            }
            expected.append(exp_history)

            # Update balance for next iteration
            initial_balance -= pmt_cntx.available_redemption_collections
            

        result = self.tranche.history_principal

        # Ensure ending balance = 0.0
        self.assertAlmostEqual(0.0, result[-1].get('current_period_ending_balance'), msg=result)

        # Ensure the lengths match
        self.assertEqual(len(expected), len(result), f"Expected {len(expected)} entries, got {len(result)}")

        # Compare each period's expected vs actual results
        for exp, res in zip(expected, result):
            for key in exp:
                # Float-safe comparison
                self.assertAlmostEqual(exp[key], res[key], msg=f"Mismatch at period {exp['period']} for key '{key}'")

    def test_interest_payment_runs(self):
        """
        Tests that multiple periods of interest payments are correctly processed
        and tracked in the tranche's paid interest history.
        """
        # Simulated payment context for 3 periods
        payment_context = [
            PaymentContext(available_revenue_collections=200e3, available_redemption_collections=0.0, pool_balance=10e6, revenue_collections=0.0, redemption_collections=0.0,),
            PaymentContext(available_revenue_collections=100e3, available_redemption_collections=0.0, pool_balance=10e6, revenue_collections=0.0, redemption_collections=0.0,),
            PaymentContext(available_revenue_collections=500e3, available_redemption_collections=0.0, pool_balance=10e6, revenue_collections=0.0, redemption_collections=0.0,)
        ]

        exp_due = round ( 10e6 * (0.06 + 0.02) / 4 , 2 )
        current_interest_due = [exp_due, exp_due, exp_due]        
        last_period_unpaid = [0,0,100e3]
        interest_on_last_period_unpaid_interest = [0,0,2e3]

        expected = []

        for i, pmt_cntx in enumerate(payment_context, 1):
            payment_run = self.tranche.apply_revenue_due(pmt_cntx, i)
            due = self.tranche.current_total_interest_due(i)
            paid = payment_run.get('revenue_funds_distributed')
            unpaid = payment_run.get('revenue_amount_unpaid')

            self.tranche.update_history_revenue_distributions(i, due, paid, unpaid)
            self.tranche.update_last_paid_and_last_unpaid_interest(paid, unpaid)

            j = i-1

            curr_int_due = current_interest_due[j]
            last_unp = last_period_unpaid[j]
            int_on_last_unp_unt = interest_on_last_period_unpaid_interest[j]

            tot_int_due = curr_int_due + last_unp + int_on_last_unp_unt

            exp_history = ({
                'period': i, 
                'current_interest_due': curr_int_due, 
                'last_period_unpaid_interest': last_unp,
                'interest_on_last_period_unpaid_interest': int_on_last_unp_unt,
                'total_interest_due': tot_int_due, 
                'current_period_distribution': min(tot_int_due, pmt_cntx.available_revenue_collections), 
                'current_period_unpaid_interest': max(tot_int_due - pmt_cntx.available_revenue_collections, 0)
            })

            expected.append(exp_history)

        result = self.tranche.history_interest

        # Ensure the test fails if result is unexpectedly empty or mismatched
        self.assertEqual(len(result), len(expected), f"Expected {len(expected)} entries, got {len(result)}")

        for exp, res in zip(expected, result):
            for key in exp:
                self.assertAlmostEqual(exp[key], res[key], msg=f"Mismatch at period {exp['period']} for key '{key}' \n expected: {exp[key]} vs actual {res[key]}")


if __name__ == '__main__':
    unittest.main()