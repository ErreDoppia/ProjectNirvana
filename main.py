
from waterfall_engine.engine import RunWaterfall, Deal
from waterfall_engine.tranche import Tranche, RevenueProcessor, RedemptionProcessor
from waterfall_engine.fees import Fee


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
    revenue_waterfall_limbs=revenue_waterfall_limbs, 
    redemption_waterfall_limbs=redemption_waterfall_limbs,
    )
    
print(my_deal.total_initial_balance)

# Run a few periods
payment_context = [
    {'available_redemption_collections': 9e6,'available_revenue_collections': 800000, 'pool_balance': 150e6},
    {'available_redemption_collections': 7.5e6,'available_revenue_collections': 850000, 'pool_balance': 150e6},
    {'available_redemption_collections': 6e6,'available_revenue_collections': 720000, 'pool_balance': 150e6}
]

RunWaterfall(my_deal).run_all_IPDs(payment_context)




#my_deal.run_all_IPDs(payment_context)  
