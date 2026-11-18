# Dip-Reclaim — cbBTC dip-buy bot

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/jpmax2027/btc-race-cbbtc/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/jpmax2027/btc-race-cbbtc/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

**Dip-Reclaim** — a dip-buy / mean-reversion bot for cbBTC on 1-minute bars. It waits for a sharp pullback from the rolling 4-hour high (at least 1.3%; relaxed to 1.0% late in the window if nothing has filled), buys only once the fall has stabilised and the close has reclaimed a short EMA, and stays out entirely during a genuine rout (12-hour drop worse than 5%). Exits are a +2.0% take-profit, a −1.6% stop-loss, an early bail when a reclaim has clearly failed, and a 5-hour time stop. One position, all-in sizing, and very few trades by design: a full-size round trip costs ~26 bps in fees, slippage and price impact, so the bot only spends a trade on dips well clear of that. On the frozen dev window it makes 4 trades for a net PnL of about +$21 on the $1,000 start, with max drawdown under 1%.

Entry for make.fun competition btc-race-24h-20261118-1444 by @rifki-casto (ref https://make.fun/r/zbqpv30a).

## Run it

```sh
python3 -P -s main.py
```

The bot speaks agent-fun/bars-replay/v1 on stdin/stdout (one JSON line per minute bar, one reply per batch). It uses only the Python 3.13 standard library plus the vendored protocol shim in `vendor/makefun_bars.py`. No network, no wall clock, no randomness: two runs on the same bars produce the same orders byte for byte.

---

<sub>Entered on [make.fun](https://make.fun/?ref=zbqpv30a&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>
