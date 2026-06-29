# SPY Implied Volatility Surface + Variance Risk Premium

Builds a live implied-volatility surface for SPY options and quantifies the
**variance risk premium** — the gap between what the options market *prices in*
(implied vol) and what *actually happens* (realized vol).

Implied vols are computed **from scratch** by inverting the Black-Scholes price
(Brent root-finder), not by reading a vendor's IV column — that's the point.

## What it does
1. **Vol surface** — pulls the full SPY option chain (yfinance), keeps liquid OTM
   options, inverts Black-Scholes-Merton (with dividend yield + T-bill rate) for
   each contract's implied vol, and renders:
   - `vol_surface.png` — the 3D surface (moneyness × expiry × IV)
   - `vol_skew.png` — the ~30-day skew (downside puts bid up vs upside calls)
   - `term_structure.png` — ATM IV across expiries
2. **Variance risk premium** — compares VIX (30-day implied) to the *subsequent*
   21-day realized vol over 12 years → `vrp.png`.

## Findings (illustrative, 2026-06-29 run)
- ATM ~30-day implied vol: **~15%**
- Mean variance risk premium (12y): **+3.5 vol points** (implied over realized)
- Implied exceeded subsequent realized **~82% of days**

**Interpretation (honest):** implied vol sits above realized the large majority
of the time — selling vol harvests that premium. But the left tail (March 2020,
where realized spiked *above* implied) is where vol sellers blow up. It's a risk
premium, not free money.

## Run
```bash
pip install -r requirements.txt
python3 run.py
```

## Methodology notes
- **OTM-only** quotes (calls for K≥S, puts for K<S) — more liquid, avoids
  put/call-parity inconsistencies.
- Mid price = (bid+ask)/2 where available, else last.
- Drops sub-7-day expiries and |moneyness| outside 0.88–1.12 (noisy wings).
- Risk-free = 13-week T-bill (^IRX); dividend yield ≈ 1.3% for SPY.
- yfinance data is delayed/retail-grade — fine for structure/teaching, not a
  production trading signal. A real desk would use clean, timestamped vendor data.

## Files
`blackscholes.py` (pricing + IV inversion) · `data.py` (market data) ·
`surface.py` (surface construction) · `run.py` (charts + VRP + findings)
