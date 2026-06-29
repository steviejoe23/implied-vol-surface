"""Raw SVI (stochastic volatility inspired) slice calibration.

Fits Gatheral's raw SVI parameterization of total implied variance to one expiry
slice, and checks the Gatheral butterfly no-arbitrage condition g(k) >= 0.

  w(k) = a + b * ( rho*(k - m) + sqrt((k - m)^2 + sigma^2) )
  k = log-moneyness log(K/S),  w = total implied variance = IV^2 * T

Reference: Gatheral & Jacquier (2014), "Arbitrage-Free SVI Volatility Surfaces".
"""
import numpy as np
from scipy.optimize import least_squares


def svi_total_variance(k, a, b, rho, m, sigma):
    return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + sigma ** 2))


def calibrate_svi(k, w):
    """Fit (a, b, rho, m, sigma) to market total variance w at log-moneyness k."""
    k = np.asarray(k, dtype=float)
    w = np.asarray(w, dtype=float)
    p0 = [max(np.min(w) * 0.5, 1e-4), 0.1, -0.3, 0.0, 0.1]
    lb = [-np.inf, 1e-6, -0.999, -1.0, 1e-4]
    ub = [np.max(w) + 1.0, 10.0, 0.999, 1.0, 5.0]

    def resid(p):
        return svi_total_variance(k, *p) - w

    res = least_squares(resid, p0, bounds=(lb, ub), max_nfev=5000)
    params = dict(zip(["a", "b", "rho", "m", "sigma"], res.x))
    rmse = float(np.sqrt(np.mean(res.fun ** 2)))
    return params, rmse


def svi_iv(k, params, T):
    w = svi_total_variance(k, **params)
    return np.sqrt(np.maximum(w, 1e-10) / T)


def butterfly_g(k, params):
    """Gatheral's g(k); g >= 0 everywhere means no butterfly arbitrage."""
    def w(x):
        return svi_total_variance(x, **params)
    h = 1e-4
    wk = w(k)
    wp = (w(k + h) - w(k - h)) / (2 * h)
    wpp = (w(k + h) - 2 * w(k) + w(k - h)) / h ** 2
    return (1 - k * wp / (2 * wk)) ** 2 - (wp ** 2 / 4) * (1 / wk + 0.25) + wpp / 2
