"""Dip-reclaim: a cbBTC dip-buy / mean-reversion bot for make.fun's btc-race.

Strategy (long only, one position, deliberately few trades):

  Entry - the price has pulled back at least DIP (1.3%) from its rolling
    LOOKBACK-minute high, the fall has stabilised (the close is back above a
    short EMA of closes and the last STAB_WIN minutes are not still sliding),
    and the long regime is not a rout (the close is not more than REGIME_DROP
    below where it was REGIME_WIN minutes ago). Then buy with all the cash:
    a full-size round trip costs roughly 26 bps in fees, slippage and impact,
    so only dips well clear of that are worth taking. If no dip that deep has
    filled by FALLBACK_AFTER batches, the threshold relaxes to FALLBACK_DIP:
    late and shallow beats never trading at all.

  Exit - take profit at +TP, stop loss at -SL, a time stop after MAXHOLD
    minutes, or an early bail if the reclaim has clearly failed (still down
    FAIL_DROP after FAIL_AFTER minutes): whichever comes first. The harness
    flattens whatever is left at the end of the window.

Everything is decided from the bars alone: no clock, no environment, no
randomness, so two runs on the same data give the same orders byte for byte.
Ratios are computed in float64 on + - * / only, each correctly rounded
(IEEE 754), so they too are identical run after run.
"""

import os
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

LOOKBACK = 240         # minutes in the rolling high a dip is measured from
DIP = 0.013            # pullback from that high that arms an entry
FALLBACK_AFTER = 900   # batches with no filled buy before the dip relaxes
FALLBACK_DIP = 0.010   # the relaxed pullback threshold
CONFIRM_SPAN = 8       # EMA span (minutes) the close must reclaim to confirm
STAB_WIN = 10          # minutes over which the fall must have stopped
STAB_MAX_FALL = 0.002  # still falling faster than this over STAB_WIN: no buy
REGIME_WIN = 720       # minutes in the regime filter's lookback
REGIME_DROP = 0.05     # a fall worse than this over REGIME_WIN blocks entries
TP = 0.020             # take profit: position worth this much over its cost
SL = 0.016             # stop loss: this much under its cost
FAIL_AFTER = 45        # minutes after which a failed reclaim is bailed on
FAIL_DROP = 0.009      # still this far under water then: sell
MAXHOLD = 300          # minutes: time stop
COOLDOWN = 60          # minutes flat after an exit before the next entry
MAX_SLIPPAGE_BPS = 150


class DipReclaim:
    def __init__(self):
        self.closes = []            # every close, as int at price_scale
        self.recent = deque(maxlen=LOOKBACK)
        self.ema = None             # float EMA of closes, CONFIRM_SPAN
        self.holding = False        # a position was in the account last batch
        self.entry_seq = -1         # batch seq whose open filled the buy
        self.ever_bought = False    # a buy has filled at some point
        self.cool = 0               # batches of cooldown left

    def on_batch(self, state, batch):
        fresh = False
        for bar in batch["bars"]:
            if bar["symbol"] != SYMBOL:
                continue
            fresh = True
            c = int(bar["c"])
            self.closes.append(c)
            self.recent.append(c)
            if self.ema is None:
                self.ema = float(c)
            else:
                k = 2.0 / (CONFIRM_SPAN + 1)
                self.ema += k * (c - self.ema)
        if self.cool > 0:
            self.cool -= 1
        held = state.positions.get(SYMBOL)
        if held is not None and not self.holding:
            # The buy decided last batch filled at this bar's open; this
            # batch is the first to report the position.
            self.entry_seq = state.seq
            self.ever_bought = True
        self.holding = held is not None
        if not fresh or state.warming_up:
            return []
        close = state.close(SYMBOL)
        if close is None:
            return []
        if held is not None:
            return self._exit(state, held, close)
        return self._entry(state, close)

    def _exit(self, state, held, close):
        value = state.value(SYMBOL, held.qty, close)
        held_bars = state.seq - self.entry_seq
        if value >= held.cost * (1.0 + TP) or value <= held.cost * (1.0 - SL):
            return [self._sell(held)]
        if held_bars >= FAIL_AFTER and value <= held.cost * (1.0 - FAIL_DROP):
            return [self._sell(held)]
        if held_bars >= MAXHOLD:
            return [self._sell(held)]
        return []

    def _entry(self, state, close):
        if self.cool > 0 or len(self.closes) < LOOKBACK + 2:
            return []
        dip = DIP
        if not self.ever_bought and state.seq > FALLBACK_AFTER:
            dip = FALLBACK_DIP
        high = max(self.recent)
        if close > high * (1.0 - dip):
            return []                       # no real pullback from the high
        if close < self.ema:
            return []                       # fall not stabilised / reclaimed
        if len(self.closes) > STAB_WIN:
            past = self.closes[-1 - STAB_WIN]
            if close < past * (1.0 - STAB_MAX_FALL):
                return []                   # still sliding: do not catch it
        if len(self.closes) > REGIME_WIN:
            past = self.closes[-1 - REGIME_WIN]
            if close < past * (1.0 - REGIME_DROP):
                return []                   # a rout, not a dip
        notional = state.cash
        if notional < int(state.hello["fees"]["min_notional_quote_units"]):
            return []
        return [{"side": "buy", "symbol": SYMBOL,
                 "notional_quote_units": notional,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]

    def _sell(self, held):
        self.cool = COOLDOWN
        return {"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS}


def main():
    bot = DipReclaim()
    makefun_bars.run(bot.on_batch)


if __name__ == "__main__":
    main()
