
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 10 22:24:32 2025

Filename: waterfall_engine.py
Author: ricca
"""

from typing import Optional
from abc import ABC, abstractmethod
from typing import TypedDict

from .settings import FREQ_MULTIPLIER
from .tranche import Tranche
from .fees import Fee
from .models import RevenueWaterfallLimb, RedemptionWaterfallLimb
from .models import RevenuePaymentRunResult, RedemptionPaymentRunResult
from .models import PaymentContext


### DEAL CLASS ###
class Deal:
    """
    Represents a securitization deal with its tranches, fees, and waterfalls.
    Contains methods to manage the deal's financial flows and history.
    """
    def __init__(self, 
                name: str, 
                tranches: list[Tranche], 
                fees: list[Fee], 
                repayment_structure: str,
                revenue_waterfall_limbs: dict[int, RevenueWaterfallLimb], 
                redemption_waterfall_limbs: dict[int, RedemptionWaterfallLimb]
                ):
        
        self.name = name
        self.tranches = tranches
        self.fees = fees

        if repayment_structure not in ['sequential', 'pro-rata']:
            raise ValueError('Invalid repayment structure. Must be "sequential" or "pro-rata".')
        self.repayment_structure = repayment_structure

        self.revenue_waterfall_limbs = revenue_waterfall_limbs
        self.redemption_waterfall_limbs = redemption_waterfall_limbs

        self.revenue_waterfall = RevenueWaterfall(self.revenue_waterfall_limbs)
        self.redemption_waterfall = RedemptionWaterfall(self.redemption_waterfall_limbs)

        self._total_initial_balance = sum(t.initial_balance for t in self.tranches)

        self._total_last_period_ending_balance = sum(t.last_period_ending_balance for t in self.tranches)

        self.history_revenue = []
        self.history_redemption = []

    @property
    def total_initial_balance(self) -> float:
        """
        Returns the total initial balance of all tranches.
        """
        return self._total_initial_balance
    
    @property
    def total_last_period_ending_balance(self) -> float:
        """
        Returns the total last period ending balance of all tranches.
        """
        return self._total_last_period_ending_balance
    
    def update_total_last_period_ending_balance(self):
        """
        Updates the total last period ending balance based on current tranche balances.
        """
        self._total_last_period_ending_balance = sum(t.last_period_ending_balance for t in self.tranches)



### PRINCIPAL ALLOCATION RULES ###
class PrincipalAllocationRules:
    def __init__(self, deal: Deal):

        self.deal = deal

    def allocate_principal(self, payment_context: PaymentContext) -> dict[str, float]:
        """
        Allocates principal repayments across tranches based on the defined structure.
        Currently supports only sequential allocation.
        """

        available_funds = payment_context.available_redemption_collections
        tranches = self.deal.tranches
        allocation: dict[str, float] = {}

        if self.deal.repayment_structure == 'sequential':
            weights = {
                tranche.name: 1.0 for tranche in tranches if tranche.last_period_ending_balance > 0
            }
        else:
            # Pro-rata allocation weights based on last period ending balance
            weights = {
                tranche.name: tranche.last_period_ending_balance / self.deal.total_last_period_ending_balance
                for tranche in tranches
            }
            # Ensure weights sum to 1
            total_weight = sum(weights.values())
 
        # Compute allocation
        for tranche in tranches:
            desired_allocation = round(weights[tranche.name] * available_funds, 2)
            payment = min(tranche.last_period_ending_balance, desired_allocation)
            if payment > 0:
                allocation[tranche.name] = payment
                available_funds -= payment

        return allocation
        

### REVENUE AND REDEMPTION WATERFALLS ###
class RevenueWaterfall:
    """
    Applies collections in priority order across revenue waterfall limbs.
    Each limb processes its due amount based on the available revenue collections.
    """
    def __init__(self, waterfall_limbs: dict[int, RevenueWaterfallLimb]):
        """
        Initialize with an ordered dictionary of waterfall limbs.
        """
        self.limbs = waterfall_limbs
        
    def apply(self, payment_context: PaymentContext, period: int) -> dict[str, dict[str, float]]:
        """
        Applies collections to each limb by priority.
        """
        results = {}
            
        for priority, limb in self.limbs.items(): 
            name = limb.name
            payment_run_payload = limb.distribute_due(payment_context, period)
            
            revenue_funds_distributed = payment_run_payload.get('revenue_funds_distributed')
            amount_unpaid = payment_run_payload.get('revenue_amount_unpaid')
            
            results[f"{priority} - {name}"] = {
                'available_cash': payment_context.available_revenue_collections,
                'amount_paid': revenue_funds_distributed,
                'amount_unpaid': amount_unpaid
                }
            
            payment_context.available_revenue_collections = max(
                payment_context.available_revenue_collections - revenue_funds_distributed, 0)
        
        results['excess_spread'] = {
            'available_cash': payment_context.available_revenue_collections,
            'amount_paid': payment_context.available_revenue_collections,
            'amount_unpaid': 0.00
            }
        return results  


class RedemptionWaterfall:
    """
    Applies collections in priority order across redemption waterfall limbs.
    Each limb processes its due amount based on the available redemption collections.
    """
    def __init__(self, waterfall_limbs: dict[int, RedemptionWaterfallLimb]):
        """
        Initialize with an ordered dictionary of waterfall limbs.
        """
        self.limbs = waterfall_limbs
        
    def apply(self, payment_context: PaymentContext, period: int) -> dict[str, dict[str, float]]:
        """
        Applies collections to each limb by priority.
        """
        results = {}
            
        for priority, limb in self.limbs.items(): 
            name = limb.name
            payment_run_payload = limb.distribute_principal_due(payment_context, period)
            
            redemption_funds_distributed = payment_run_payload.get('redemption_funds_distributed')
            amount_unpaid = payment_run_payload.get('redemption_amount_unpaid')

            results[f"{priority} - {name}"] = {
                'available_cash': payment_context.available_redemption_collections,
                'amount_paid': redemption_funds_distributed,
                'amount_unpaid': amount_unpaid
                }
            
            payment_context.available_redemption_collections = max(
                payment_context.available_redemption_collections - redemption_funds_distributed, 0.0)

        results['excess_spread'] = {
            'available_cash': payment_context.available_redemption_collections,
            'amount_paid': payment_context.available_redemption_collections,
            'amount_unpaid': 0.00
            }
        
        return results


### RUN WATERFALL ENGINE ###
class RunWaterfall:
    def __init__(self, deal: Deal):
        """
        Initialize the securitization deal with waterfall limbs and structure.
        """
        self.deal = deal
        
    def run_IPD(self, payment_context: PaymentContext, period: int):
        """
        Executes one Interest Payment Date logic.
        """
        principal_allocations = PrincipalAllocationRules(self.deal).allocate_principal(payment_context)
        payment_context.principal_allocations = principal_allocations

        if payment_context.principal_allocations == principal_allocations:
            # Apply revenue and redemption waterfalls
            rev_waterfall_results = self.deal.revenue_waterfall.apply(payment_context, period)
            red_waterfall_results = self.deal.redemption_waterfall.apply(payment_context, period)
        else:
            raise ValueError("Principal allocations do not match expected allocations.")
        
        snapshot_revenue = {period: rev_waterfall_results}
        snapshot_redemption = {period: red_waterfall_results}

        self.deal.history_revenue.append(snapshot_revenue)
        self.deal.history_redemption.append(snapshot_redemption)

        print(f"IPD number {period}")
        print(f"Interest: {self.deal.history_revenue[period-1]}")
        print("")
        print(f"Principal: {self.deal.history_redemption[period-1]}")
        print("")
        
    def run_all_IPDs(self, payment_contexts: list[PaymentContext]):
        """
        Executes all Interest Payment Dates for the given payment context.
        """
        for i, pmt_cntx in enumerate(payment_contexts, 1):
            self.run_IPD(pmt_cntx, i)
