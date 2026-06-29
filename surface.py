"""Build the implied-volatility surface from an option chain.

Uses OTM options only (calls for K>=S, puts for K<S) — they're more liquid and
avoid put/call parity inconsistencies — and computes IV from the mid price via
our own Black-Scholes inversion.
"""
import datetime
import numpy as np
import pandas as pd
from blackscholes import implied_vol

DIV_YIELD = 0.013  # SPY approx continuous dividend yield


def _mid(row):
    bid = row.get("bid", 0) or 0
    ask = row.get("ask", 0) or 0
    if bid > 0 and ask > 0:
        return (bid + ask) / 2.0
    return row.get("lastPrice", 0) or 0


def build_surface(chains, S, r, q=DIV_YIELD, m_lo=0.88, m_hi=1.12, min_days=7):
    today = datetime.date.today()
    rows = []
    for _, o in chains.iterrows():
        K = float(o["strike"])
        is_call = bool(o["is_call"])
        days = (datetime.date.fromisoformat(o["expiry"]) - today).days
        if days < min_days:  # drop noisy ultra-short expiries
            continue
        T = days / 365.0
        m = K / S
        if not (m_lo <= m <= m_hi):
            continue
        # OTM only
        if is_call and K < S:
            continue
        if (not is_call) and K >= S:
            continue
        mid = _mid(o)
        if mid <= 0:
            continue
        iv = implied_vol(mid, S, K, T, r, q, is_call)
        if not np.isfinite(iv) or iv <= 0.03 or iv > 1.5:
            continue
        rows.append({"T": T, "K": K, "moneyness": m, "iv": iv, "is_call": is_call})
    return pd.DataFrame(rows)
