# SPY Implied Volatility Surface and the Variance Risk Premium

This project builds an implied-volatility surface for SPY options and measures the
variance risk premium: the gap between the volatility the options market prices in
and the volatility that actually shows up.

I compute every implied vol myself by inverting the Black-Scholes price with a
Brent root-finder, rather than reading a data vendor's IV column. That inversion
is the part worth doing.

## What it does
1. Pulls the full SPY option chain, keeps liquid out-of-the-money options, and
   solves Black-Scholes-Merton (with a dividend yield and T-bill rate) for each
   contract's implied vol. It then plots:
   - `vol_surface.png`: the 3D surface across moneyness and expiry
   - `vol_skew.png`: the roughly 30-day skew (downside puts priced richer than calls)
   - `term_structure.png`: at-the-money IV across expiries
2. Compares VIX (30-day implied vol) to the realized vol over the following 21 days,
   across 12 years, and plots the result in `vrp.png`.

## What I found (run on 2026-06-29)
- At-the-money 30-day implied vol: about 15%
- Average variance risk premium over 12 years: about +3.5 vol points (implied above
  realized)
- Implied vol came in above the realized vol that followed on roughly 82% of days

So the options market tends to overprice near-term volatility, and selling vol
collects that premium most of the time. The exception is what matters: in March 2020
realized vol shot above implied, which is where short-vol positions take their worst
losses. It's a risk premium, not free money.

## Arbitrage-free SVI calibration
A raw scatter of implied vols is not desk-quality. `svi.py` fits Gatheral's raw SVI
parameterization to the ~30-day slice and checks the butterfly no-arbitrage
condition g(k) >= 0. The latest fit has an RMSE near 0.0001 and min g(k) well above
zero, so the calibrated smile is arbitrage-free (`svi_fit.png`).

## The honest version of harvesting the premium
`vrp_strategy.py` simulates selling one-month variance every month and shows the
whole picture, not just the average. It wins about 81% of months with a Sharpe near
0.7, but the worst month is roughly -85 vol points and the conditional loss (CVaR)
is about -29 (`vrp_strategy.png`). That is the point: the premium is real, and so is
the steamroller.

## Run it
```bash
pip install -r requirements.txt
python3 run.py            # surface, skew, term structure, SVI fit, VRP
python3 vrp_strategy.py   # honest short-vol carry with tail and drawdown
```

## Notes on method
- Out-of-the-money quotes only (calls above spot, puts below). They're more liquid
  and avoid put/call parity issues.
- Mid price is (bid+ask)/2 where both are available, otherwise last price.
- Drops expiries under 7 days and moneyness outside 0.88 to 1.12, where the data
  gets noisy.
- Risk-free rate from the 13-week T-bill (^IRX); SPY dividend yield assumed near 1.3%.
- Data comes from yfinance, which is delayed and retail-grade. Fine for studying the
  structure, not something I'd trade on. A real desk would use clean vendor data.

## Layout
`blackscholes.py` (pricing and IV inversion), `data.py` (market data),
`surface.py` (surface construction), `svi.py` (SVI calibration and no-arb check),
`run.py` (charts, SVI fit, VRP), `vrp_strategy.py` (honest short-vol carry).
