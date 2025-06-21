
from .settings import FREQ_MULTIPLIER
from .models import RevenueWaterfallLimb, RedemptionWaterfallLimb
from .models import RevenuePaymentRunResult, RedemptionPaymentRunResult


# Represents a Tranche in the capital structure, receiving interest and principal
class Tranche:
    def __init__(
            self, 
            name: str, 
            initial_balance: float, 
            reference_rate: float,
            margin: float, 
            maturity: int,
            payment_frequency: str,
            trigger_default_on_missed_payment: bool = False,
            write_off_unpaid_interest: bool = False,
            interest_on_unpaid_interest: bool = True,
            step_up_margin: float = 0.0, 
            step_up_date: float = None,
            method: str = None,
            repayment_structure: str = 'sequential',
            ):
        
        """
        A debt tranche that tracks interest and principal cash flows over time
        within a waterfall structure.
        """

        self._name = name

        if initial_balance < 0:
            raise ValueError('Balance cannot be negative')
        else:
            self.initial_balance = initial_balance

        self.reference_rate = reference_rate
        self.margin = margin
        self.maturity = maturity

        if payment_frequency not in FREQ_MULTIPLIER:
            raise ValueError(f'Invalid payment frequency: {payment_frequency}')
        self.payment_frequency = payment_frequency
        
        self.trigger_default_on_missed_payment = trigger_default_on_missed_payment
        self.write_off_unpaid_interest = write_off_unpaid_interest
        self.accrue_interest_on_arrears =  interest_on_unpaid_interest
        
        self.step_up_margin = step_up_margin
        self.step_up_date = step_up_date
        self.method = method

        if repayment_structure not in ['sequential', 'pro-rata']:
            raise ValueError('Invalid repayment structure')
        self.repayment_structure = repayment_structure

        ### CONTEXT VARIABLES ### 
        ### Interest
        self._last_period_due_interest = 0.0
        self._last_period_paid_interest = 0.0
        self._last_period_unpaid_interest = 0.0

        ### Principal
        self._last_period_ending_balance = self.initial_balance 
        self._current_period_ending_balance = 0.0

        self._last_period_paid_principal = 0.0

        ### Logging ###
        self.total_paid_interest = 0.0
        self.total_unpaid_interest = 0.0

        self.history_interest = []
        self.history_principal = []
        
    @property
    def name(self):
        """Returns the name of the tranche."""
        return self._name

    @property  
    def last_period_due_interest(self):
        """Interest due in previous period."""
        return self._last_period_due_interest
    
    @property
    def last_period_paid_interest(self):
        """Interest actually paid in previous period."""
        return self._last_period_paid_interest

    @property
    def last_period_unpaid_interest(self):
        """
        Returns unpaid interest from prior period unless written off.
        """
        if not self.write_off_unpaid_interest:
            return self._last_period_unpaid_interest
        else:
            return 0.0   

    @property
    def last_period_ending_balance(self):
        """Principal remaining at last period end."""
        return self._last_period_ending_balance

    @property
    def current_period_ending_balance(self):
        """Balance forecasted after current payments."""
        return self._current_period_ending_balance 
    
    def current_period_margin(self, period: int) -> float:
        """
        Returns the applicable margin (step-up if triggered).
        """
        if self.step_up_date and period >= self.step_up_date:
            return self.step_up_margin
        return self.margin 
    
    def current_all_in_rate(self, period: int) -> float:
        """
        Returns total rate = reference + margin.
        """
        return self.current_period_margin(period) + self.reference_rate
    
    def current_interest_on_last_period_unpaid_interest(self, period: int) -> float: 
        """
        Interest accrued on last period’s arrears.
        """
        arrears = self.last_period_unpaid_interest
        interest_rate = self.current_all_in_rate(period)
        multiplier = FREQ_MULTIPLIER.get(self.payment_frequency)
        interest_on_arrears = arrears * interest_rate / multiplier
        return interest_on_arrears
    
    def current_interest_due(self, period: int) -> float:
        """
        Interest due this period based on ending balance.
        """
        multiplier = FREQ_MULTIPLIER.get(self.payment_frequency)
        due = self.current_all_in_rate(period) * self.last_period_ending_balance / multiplier  
        return due
    
    def current_total_interest_due(self, period: int) -> float:
        """
        Total interest due including arrears and interest on arrears.
        """
        due = self.current_interest_due(period)
        arrears = self.last_period_unpaid_interest
        int_on_arrears = self.current_interest_on_last_period_unpaid_interest(period)
        return due + arrears + int_on_arrears      
    
    def distribute_due(self, payment_context: dict, period: int) -> RevenuePaymentRunResult:
        """
        Pays interest due.
        """
        available_revenue_funds = payment_context.get('available_revenue_collections',0.0)
        pool_balance = payment_context.get('pool_balance', 0.0)

        interest_due = self.current_total_interest_due(period)    
        revenue_funds_distributed = min(interest_due, available_revenue_funds)
        interest_unpaid = interest_due - revenue_funds_distributed
                                                  
        payment_run_return_payload = {
            'revenue_funds_distributed' : revenue_funds_distributed,
            'revenue_amount_unpaid' : interest_unpaid,
        }
        
        self.update_history_interest(period, revenue_funds_distributed, interest_unpaid)
        self.update_last_paid_and_last_unpaid_interest(revenue_funds_distributed, interest_unpaid)
        self.update_total_paid_and_total_unpaid_interest(revenue_funds_distributed, interest_unpaid)
        
        
        return payment_run_return_payload
    
    def update_history_interest(self, period: int, paid: float, unpaid: float):
        """Stores interest history for analysis or reporting."""
        due = self.current_interest_due(period)
        arrears = self.last_period_unpaid_interest
        interest_on_arrears = self.current_interest_on_last_period_unpaid_interest(period)
        total_due = paid + unpaid
                        
        self.history_interest.append({
            'period': period, 
            'current_interest_due': due, 
            'last_period_unpaid_interest': arrears,
            'interest_on_last_period_unpaid_interest': interest_on_arrears,
            'total_interest_due': total_due, 
            'current_period_distribution': paid, 
            'current_period_unpaid_interest': unpaid
            })
    
    def update_last_paid_and_last_unpaid_interest(self, paid: float, unpaid: float):      
        """Tracks last period paid/unpaid interest."""
        self._last_period_paid_interest = paid
        self._last_period_unpaid_interest = unpaid
    
    def update_total_paid_and_total_unpaid_interest(self, paid: float, unpaid: float):
        """Accumulates total paid/unpaid interest over time."""
        self.total_paid_interest += paid
        self.total_unpaid_interest += unpaid

    def update_last_period_ending_balance(self, unpaid: float):
        """Updates balance for principal repayment period."""
        self._last_period_ending_balance = unpaid


    def update_last_period_paid_principal(self, paid):
        """Stores principal paid in last period."""
        self._last_period_paid_principal = paid               

    def update_history_principal(self, period: int, paid: float, unpaid: float):
        """Stores principal payment history."""
        self.history_principal.append({
            'period': period, 
            'last_period_ending_balance': self.last_period_ending_balance,
            'current_period_repayments': paid,
            'current_period_ending_balance': unpaid
        })

    def distribute_principal_due(self, payment_context: dict, period: int) -> dict:
        """
        Pays principal due.
        """
        available_redemption_funds = payment_context.get('available_redemption_collections',0.0)
        
        principal_due = self.current_period_principal_due()
        redemption_funds_distributed = min(principal_due, available_redemption_funds)
        redemption_amount_unpaid = self.last_period_ending_balance - redemption_funds_distributed
        
        payment_run_return_payload = {
            'redemption_funds_distributed' : redemption_funds_distributed,
            'redemption_amount_unpaid' : redemption_amount_unpaid,
        }
        
        # update class trackers
        self.update_history_principal(period, redemption_funds_distributed, redemption_amount_unpaid)
        self.update_last_period_paid_principal(redemption_funds_distributed)
        self.update_last_period_ending_balance(redemption_amount_unpaid)
        
        return payment_run_return_payload
    
    ### TODO ###
    def current_period_principal_due(self):
        """Principal due this period based on allocation rules"""
        if self.repayment_structure == 'sequential':
            return self.last_period_ending_balance
        else:
            pass
    

class RevenueProcessor(RevenueWaterfallLimb):
    def __init__(self, tranche: Tranche):
        self._tranche = tranche
        
    @property
    def name(self):
        return self._tranche.name
    
    def distribute_due(self, payment_context: dict, period: int):
        return self._tranche.distribute_due(payment_context, period)


class RedemptionProcessor(RedemptionWaterfallLimb):
    def __init__(self, tranche: Tranche):
        self._tranche = tranche
    
    @property
    def name(self):
        return self._tranche.name
    
    def distribute_principal_due(self, payment_context, period: int):
        return self._tranche.distribute_principal_due(payment_context, period)
    



    

 
