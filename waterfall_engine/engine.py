
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

class Deal:
    def __init__(self, 
                name: str, 
                tranches: list[Tranche], 
                fees: list[Fee], 
                revenue_waterfall_limbs: dict[int, RevenueWaterfallLimb], 
                redemption_waterfall_limbs: dict[int, RedemptionWaterfallLimb]
                ):
        
        self.name = name
        self.tranches = tranches
        self.fees = fees

        self.revenue_waterfall_limbs = revenue_waterfall_limbs
        self.redemption_waterfall_limbs = redemption_waterfall_limbs

        self.revenue_waterfall = RevenueWaterfall(self.revenue_waterfall_limbs)
        self.redemption_waterfall = RedemptionWaterfall(self.redemption_waterfall_limbs)

        self.total_initial_balance = 0.0
        for t in self.tranches:
            self.total_initial_balance += t.initial_balance

        self.history_revenue = []
        self.history_redemption = []


# ==================================================================
# ======================PRINCIPAL ALLOCATION RULES==================    
# ==================================================================
class PrincipalAllocationRules:
    """
    Placeholder for future principal allocation rules.
    Currently, all tranches are sequential.
    """
    def __init__(self, repayment_structure: str = 'sequential'):
        if repayment_structure not in ['sequential', 'pro-rata']:
            raise ValueError('Invalid repayment structure')
        self.repayment_structure = repayment_structure

    def allocate_principal(self, tranches: list[Tranche], available_redemption_funds: float) -> dict[str, float]:
        """
        Allocates principal repayments across tranches based on the defined structure.
        Currently supports only sequential allocation.
        """
        if self.repayment_structure == 'sequential':
            # Sequentially pay down tranches until funds run out
            allocation = {}
            for tranche in tranches:
                if available_redemption_funds <= 0:
                    break
                payment = min(tranche.last_period_ending_balance, available_redemption_funds)
                allocation[tranche.name] = payment
                available_redemption_funds -= payment
            return allocation
        else:
            raise NotImplementedError("Pro-rata allocation not implemented yet.")

# Applies collections in priority order across limbs
class RevenueWaterfall:
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
                'available_cash': payment_context.get('available_revenue_collections'),
                'amount_paid': revenue_funds_distributed,
                'amount_unpaid': amount_unpaid
                }
            
            payment_context['available_revenue_collections'] = max(
                payment_context.get('available_revenue_collections', 0.0) - revenue_funds_distributed,0)
        
        results['excess_spread'] = {
            'available_cash': payment_context.get('available_revenue_collections',0.0),
            'amount_paid': payment_context.get('available_revenue_collections',0.0),
            'amount_unpaid': 0.00
            }
        return results  


# Applies collections in priority order across limbs
class RedemptionWaterfall:
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
                'available_cash': payment_context.get('available_redemption_collections'),
                'amount_paid': redemption_funds_distributed,
                'amount_unpaid': amount_unpaid
                }
            
            payment_context['available_redemption_collections'] = max(
                payment_context.get('available_redemption_collections', 0.0) - redemption_funds_distributed,0.0)
            
        results['excess_spread'] = {
            'available_cash': payment_context.get('principal',0.0),
            'amount_paid': payment_context.get('principal',0.0),
            'amount_unpaid': 0.00
            }
        
        return results


# Waterfall execution
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
        rev_waterfall_results = self.deal.revenue_waterfall.apply(payment_context, period)
        red_waterfall_results = self.deal.redemption_waterfall.apply(payment_context, period)

        snapshot_revenue = {period: rev_waterfall_results}
        snapshot_redemption = {period: red_waterfall_results}

        self.deal.history_revenue.append(snapshot_revenue)
        self.deal.history_redemption.append(snapshot_redemption)

        print(f"IPD number {period}")
        print(f"Interest: {self.deal.history_revenue[period-1]}")
        print("")
        print(f"Principal: {self.deal.history_redemption[period-1]}")
        print("")
        
    def run_all_IPDs(self, payment_context: PaymentContext):
        """
        Executes all Interest Payment Dates for the given payment context.
        """
        for i, pmt_cntx in enumerate(payment_context, 1):
            self.run_IPD(pmt_cntx, i)
