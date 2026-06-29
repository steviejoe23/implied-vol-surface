"""Market data: spot, risk-free rate, option chains, and VIX/SPY history."""
import datetime
import numpy as np
import pandas as pd
import yfinance as yf


def _last_close(ticker):
    px = yf.download(ticker, period="5d", auto_adjust=True, progress=False)["Close"]
    return float(px.dropna().iloc[-1])


def get_spot(ticker="SPY"):
    return _last_close(ticker)


def get_riskfree():
    """13-week T-bill yield (^IRX) as a decimal; fallback 4%."""
    try:
        return _last_close("^IRX") / 100.0
    except Exception:
        return 0.04


def get_chains(ticker="SPY", max_expiries=12):
    """Concatenate calls+puts across the nearest `max_expiries` expiries."""
    t = yf.Ticker(ticker)
    try:
        expiries = list(t.options)[:max_expiries]
    except Exception:
        return pd.DataFrame()
    frames = []
    for e in expiries:
        try:
            ch = t.option_chain(e)
        except Exception:
            continue
        for df, is_call in [(ch.calls, True), (ch.puts, False)]:
            d = df.copy()
            d["expiry"] = e
            d["is_call"] = is_call
            frames.append(d)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def get_vix_spy(years=12):
    """Daily SPY close + VIX close for the variance-risk-premium analysis."""
    raw = yf.download(["SPY", "^VIX"], period=f"{years}y",
                      auto_adjust=True, progress=False)
    close = raw["Close"]
    return close["SPY"].dropna(), close["^VIX"].dropna()
