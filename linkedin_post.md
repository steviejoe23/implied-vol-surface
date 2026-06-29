# LinkedIn post draft

> Edit the voice to your own. Attach **vol_surface.png** (the hero image) and
> **vrp.png** (the payoff). Post the surface as the first image — it's the hook.

---

**Draft A — the "honest finding" angle (recommended):**

I built an implied-volatility surface for SPY from scratch — inverting Black-Scholes on the full options chain rather than trusting a data vendor's IV column — and then asked one question: does the options market overprice risk?

Over the last 12 years, implied volatility (VIX) sat *above* the volatility that actually showed up ~82% of the time, averaging +3.5 vol points. That gap is the variance risk premium — compensation for insuring everyone else's tail risk.

The catch is in the chart: in March 2020, realized vol blew *through* implied. That's where vol sellers who mistook the premium for free money got carried out.

A risk premium, not a free lunch. Built in Python (Black-Scholes IV inversion via Brent, VIX vs forward-realized over 12y). Code in comments.

#quant #volatility #optionstrading #python #quantitativefinance

---

**Draft B — the "I built this" angle:**

Spent the weekend building a live implied-volatility surface for SPY.

Every point on this surface is an implied vol I solved for by inverting the Black-Scholes price on a real option quote — ~1,000 contracts across 8 expiries. You can see the two things every options trader watches: the downside skew (puts bid up for crash protection) and the term structure.

Then I measured the variance risk premium: implied vol has averaged 3.5 points above subsequent realized vol over 12 years — but not in March 2020, when it inverted. That single exception is the whole risk.

Python + Black-Scholes + a Brent root-finder. Repo in comments.

#quantitativefinance #volatility #python #options
