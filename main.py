
from waterfall_engine.deal import Deal
from waterfall_engine.engine import RunWaterfall
from waterfall_engine.tranche import Tranche
from waterfall_engine.fees import Fee
from waterfall_engine.models import PaymentContext, RevenueProcessor, RedemptionProcessor


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

my_deal = Deal(
    name="RR25-1",
    tranches=[tranche_a, tranche_b],
    fees=[issuer_profit, servicer_fee],
    repayment_structure="pro-rata",
    revenue_waterfall_limbs=revenue_waterfall_limbs, 
    redemption_waterfall_limbs=redemption_waterfall_limbs,
    )


# Run a few periods
payment_context: list[PaymentContext] = [
    PaymentContext(available_redemption_collections=1.5e6, available_revenue_collections=1e6, pool_balance=150e6),
    PaymentContext(available_redemption_collections=1.5e6, available_revenue_collections=1e6, pool_balance=150e6),
    PaymentContext(available_redemption_collections=1.5e6, available_revenue_collections=1e6, pool_balance=150e6)
]

RunWaterfall(my_deal).run_all_IPDs(payment_context)
