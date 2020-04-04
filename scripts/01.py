from modules.source import Asset
from modules.strategy import AdaptivePQ
from modules.strategy.analysis import Optimization

btc_ltc = Asset("BTC_LTC", candlestick_period="5 min", start='3 Months',
                end='Now').date_as_datetime()

strategy = AdaptivePQ(btc_ltc.as_dataframe())

params = dict(rsi_n=2, ema_n=80, lower_limit=40, upper_limit=60, lending_rate=.02,
              stop_loss=.85, acc_stop_loss=.7)
ledger = strategy.describe(**params)
ledger.plot(figsize=(20, 10),
            cols=("profit", "acc_profit", "buy_and_hold", "sell_and_hold", "normalized_close"))

ev = strategy.describe(**params)

print(ledger.total_profit, ledger.buy_and_hold_profit, ledger.sell_and_hold_profit)
print(ev.total_profit, ev.buy_and_hold_profit, ev.sell_and_hold_profit)

analysis = Optimization(strategy, lower_limit=40, upper_limit=60, stop_loss=.85, leverage=1)
opt_res = analysis.grid_search(
    bounds=[
        ("rsi_n", 2, 30),
        ("ema_n", 75, 200),
    ],
    max_iter=500
)

print(opt_res)
