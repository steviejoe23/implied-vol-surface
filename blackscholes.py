"""Black-Scholes pricing, vega, and implied-volatility inversion.

We compute implied vol ourselves (Brent root-find on the BS price) rather than
trusting a data vendor's IV column — that's the point of the exercise.
"""
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq


def bs_price(S, K, T, r, sigma, q=0.0, call=True):
    """Black-Scholes-Merton price with continuous dividend yield q."""
    if T <= 0 or sigma <= 0:
        return max(S - K, 0.0) if call else max(K - S, 0.0)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if call:
        return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)


def bs_vega(S, K, T, r, sigma, q=0.0):
    if T <= 0 or sigma <= 0:
        return 0.0
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    return S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T)


def implied_vol(price, S, K, T, r, q=0.0, call=True):
    """Invert BS for sigma via Brent. Returns NaN if price violates no-arb."""
    if T <= 0 or price <= 0:
        return np.nan
    if call:
        intrinsic = max(S * np.exp(-q * T) - K * np.exp(-r * T), 0.0)
    else:
        intrinsic = max(K * np.exp(-r * T) - S * np.exp(-q * T), 0.0)
    if price < intrinsic - 1e-6:
        return np.nan
    try:
        return brentq(lambda s: bs_price(S, K, T, r, s, q, call) - price,
                      1e-4, 5.0, maxiter=100, xtol=1e-6)
    except (ValueError, RuntimeError):
        return np.nan
