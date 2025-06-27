
from typing import cast
from .settings import FREQ_MULTIPLIER
from .calculations import InterestAmountCalculation
from .models import PaymentContext
from .models import ApplyAmountDueResult

### TRANCHE CLASS ###
class Tranche:
    """
    A debt tranche that tracks interest and principal cash flows over time
    within a waterfall structure.
    Parameters
    ----------      
    name : str
        Name of the tranche.
    initial_balance : float
        Initial principal balance of the tranche.   
    reference_rate : float
        Reference rate (e.g. LIBOR, SOFR) for interest calculations.
    margin : float
        Margin added to the reference rate for total interest rate.         
    maturity : int
        Maturity period in months.
    payment_frequency : str
        Frequency of interest payments (e.g. 'M' for monthly, 'Q' for quarterly).
    trigger_default_on_missed_payment : bool
        Whether to trigger default if interest payment is missed.
    write_off_unpaid_interest : bool
        Whether to write off unpaid interest instead of carrying it forward.
    interest_on_unpaid_interest : bool
        Whether to accrue interest on unpaid interest from previous periods.
    step_up_margin : float
        Additional margin to apply after step-up date.
    step_up_date : int
        Period after which step-up margin applies (e.g. month number).
    method : str
        Method for interest calculation (e.g. 'act/360', '30/360').
    repayment_structure : str
        Structure for principal repayments ('sequential' or 'pro-rata').
    """
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
            step_up_date: int = None,
            method: str = None, #TODO: implement improved method for interest calculation, i.e. 'act/360' or '30/360'
            repayment_structure: str = 'sequential',
            ):

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

        # TODO: THINK ABOUT REPAYMENT STRUCTURE FOR A CLASS. IF 
        # SEQUENTIAL VS PRO-RATA IS HANDLED IN THE DEAL, THIS CAN BE REMOVED
        # HOWEVER, THIS MAY STILL BE USEFUL TO IMPLEMENT REDEMPTIONS IN 
        # THE REVENUE WATERFALL
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
        self._last_period_paid_principal = 0.0
        self._current_period_ending_balance = 0.0

        ### Totals
        self._total_paid_interest = 0.0
        self._total_unpaid_interest = 0.0

        self.history_interest = []
        self.history_principal = []

    ### PROPERTIES  
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
    
    # Current interest rate methods
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
    
    # Interest amount calculations
    def current_interest_on_last_period_unpaid_interest(self, period: int) -> float: 
        """
        Interest accrued on last period’s arrears.
        """
        arrears = self.last_period_unpaid_interest
        interest_rate = self.current_all_in_rate(period)
        interest_on_arrears = InterestAmountCalculation.calculate(
            balance=arrears, 
            interest_rate=interest_rate, 
            payment_frequency=self.payment_frequency, 
            method=self.method
            )
        return interest_on_arrears
    
    def current_interest_due(self, period: int) -> float:
        """
        Interest due this period based on ending balance.
        """
        due = InterestAmountCalculation.calculate(
            balance=self.last_period_ending_balance, 
            interest_rate=self.current_all_in_rate(period), 
            payment_frequency=self.payment_frequency, 
            method=self.method
        )
        return due

    def current_total_interest_due(self, period: int) -> float:
        """
        Total interest due including arrears and interest on arrears.
        """
        due = self.current_interest_due(period)
        arrears = self.last_period_unpaid_interest
        int_on_arrears = self.current_interest_on_last_period_unpaid_interest(period)
        return due + arrears + int_on_arrears


    def update_history_revenue_distributions(self, period: int, due: float, paid: float, unpaid: float):
        """Stores interest history for analysis or reporting."""
        
        current_interest_due = self.current_interest_due(period)
        arrears = self.last_period_unpaid_interest
        interest_on_arrears = self.current_interest_on_last_period_unpaid_interest(period)
                                
        self.history_interest.append({
            'period': period, 
            'current_interest_due': current_interest_due, 
            'last_period_unpaid_interest': arrears,
            'interest_on_last_period_unpaid_interest': interest_on_arrears,
            'total_interest_due': due, 
            'current_period_distribution': paid, 
            'current_period_unpaid_interest': unpaid
            })
        
    def update_history_redemption_distributions(self, period: int, paid: float, unpaid: float):
        """Stores principal payment history."""
        self.history_principal.append({
            'period': period, 
            'last_period_ending_balance': self.last_period_ending_balance,
            'current_period_repayments': paid,
            'current_period_ending_balance': unpaid
        })
    
    def update_last_paid_and_last_unpaid_interest(self, due: float, paid: float, unpaid: float):      
        """Tracks last period paid/unpaid interest."""
        self._last_period_due_interest = due
        self._last_period_paid_interest = paid
        self._last_period_unpaid_interest = unpaid
    
    def update_total_paid_and_total_unpaid_interest(self, paid: float, unpaid: float):
        """Accumulates total paid/unpaid interest over time."""
        self._total_paid_interest += paid
        self._total_unpaid_interest += unpaid

    def update_last_period_principal(self, paid: float, unpaid: float):
        """Updates balance for principal repayment period."""
        self._last_period_ending_balance = unpaid
        self._last_period_paid_principal = paid               

    def apply_amount_due(self, payment_context: PaymentContext, period: int, waterfall_type: str): 
        if waterfall_type == "revenue":
            return self._apply_revenue_due(payment_context, period)
        elif waterfall_type == "redemption":
            return self._apply_redemption_due(payment_context, period)
    
    # Distribution methods for Revenue and Redemption Waterfall limbs    
    def _apply_revenue_due(self, payment_context: PaymentContext, period: int) -> ApplyAmountDueResult:
        """
        Pays interest due.
        """
        available_revenue_funds = payment_context.available_cash
        pool_balance = payment_context.pool_balance

        interest_due = self.current_total_interest_due(period)    
        revenue_funds_distributed = min(interest_due, available_revenue_funds)
        interest_unpaid = interest_due - revenue_funds_distributed
                                                  
        payment_run_return_payload = {
            'amount_due': interest_due,
            'amount_paid' : revenue_funds_distributed,
            'amount_unpaid' : interest_unpaid,
        }
                
        return ApplyAmountDueResult(**payment_run_return_payload)

    def _apply_redemption_due(self, payment_context: PaymentContext, period: int) -> ApplyAmountDueResult:
        """
        Pays principal due.
        """
        available_redemption_funds = payment_context.available_cash
        
        principal_due = payment_context.principal_allocations.get(self.name, 0.0)
        redemption_funds_distributed = min(principal_due, available_redemption_funds)
        redemption_amount_unpaid = self.last_period_ending_balance - redemption_funds_distributed
        
        payment_run_return_payload = {
            'amount_due': principal_due,
            'amount_paid': redemption_funds_distributed,
            'amount_unpaid': redemption_amount_unpaid,
        }
        
        return ApplyAmountDueResult(**payment_run_return_payload)
