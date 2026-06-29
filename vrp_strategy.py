"""Honest variance-risk-premium harvest: a short-volatility carry strategy.

Each month, sell one-month variance at the implied level (VIX) and realize the
volatility that actually follows. Most months collect a premium; the point of
this script is to show the tail, not hide it: the worst month, the conditional
loss (CVaR), and the drawdown of harvesting the premium.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from data import get_vix_spy

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    spy, vix = get_vix_spy(years=12)
    rets = spy.pct_change()
    fwd_rv = rets.rolling(21).std().shift(-21) * np.sqrt(252) * 100
    df = pd.DataFrame({"VIX": vix, "fwd_RV": fwd_rv}).dropna()
    m = df.resample("ME").last().dropna()

    # short variance swap P&L per unit vega, expressed in vol points
    # (VIX^2 - RV^2) / (2*VIX) ~ implied minus realized, the premium you collect
    m["pnl"] = (m["VIX"] ** 2 - m["fwd_RV"] ** 2) / (2 * m["VIX"])
    cum = m["pnl"].cumsum()
    dd = cum - cum.cummax()

    pos = (m["pnl"] > 0).mean() * 100
    mean = m["pnl"].mean()
    worst = m["pnl"].min()
    cvar5 = m["pnl"][m["pnl"] <= m["pnl"].quantile(0.05)].mean()
    sharpe = m["pnl"].mean() / m["pnl"].std() * np.sqrt(12)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1]})
    ax1.plot(cum.index, cum.values, lw=1.8, color="#2563eb")
    ax1.set_ylabel("Cumulative premium (vol points)")
    ax1.set_title("Short-volatility carry: harvesting the variance risk premium")
    ax1.grid(True, alpha=0.3)
    ax2.fill_between(dd.index, dd.values, 0, color="red", alpha=0.4)
    ax2.set_ylabel("Drawdown")
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    out = os.path.join(HERE, "vrp_strategy.png")
    plt.savefig(out, dpi=130)
    plt.close()

    print("=== Short-vol carry (monthly, 12 years) ===")
    print(f"Positive months:        {pos:.0f}%")
    print(f"Mean premium / month:   {mean:+.2f} vol points")
    print(f"Annualized Sharpe:      {sharpe:.2f}")
    print(f"Worst month:            {worst:+.2f} vol points")
    print(f"CVaR (worst 5%):        {cvar5:+.2f} vol points")
    print(f"Max drawdown:           {dd.min():.1f} vol points")
    print("\nThe strategy wins most months and has a respectable Sharpe, but the worst "
          "month and the CVaR show the catch: harvesting the premium means picking up "
          "pennies in front of the occasional steamroller (March 2020).")
    print("Wrote", out)


if __name__ == "__main__":
    main()
