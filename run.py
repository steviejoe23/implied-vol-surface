"""Build the SPY implied-volatility surface + variance-risk-premium analysis,
save charts, and print findings.

  python3 run.py
Outputs: vol_surface.png, vol_skew.png, term_structure.png, vrp.png
"""
import os
import datetime
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from scipy.interpolate import griddata

from data import get_spot, get_riskfree, get_chains, get_vix_spy
from surface import build_surface
from svi import calibrate_svi, svi_total_variance, butterfly_g

HERE = os.path.dirname(os.path.abspath(__file__))
TICKER = "SPY"


def plot_surface(df, S):
    x, y, z = df["moneyness"].values, df["T"].values, df["iv"].values * 100
    xi = np.linspace(x.min(), x.max(), 40)
    yi = np.linspace(y.min(), y.max(), 40)
    XI, YI = np.meshgrid(xi, yi)
    ZI = griddata((x, y), z, (XI, YI), method="linear")
    fig = plt.figure(figsize=(11, 7))
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(XI, YI, ZI, cmap="viridis", alpha=0.9, linewidth=0,
                           antialiased=True)
    ax.scatter(x, y, z, c="black", s=5, alpha=0.25)
    ax.set_xlabel("Moneyness (K/S)")
    ax.set_ylabel("Time to expiry (years)")
    ax.set_zlabel("Implied vol (%)")
    ax.set_title(f"{TICKER} Implied Volatility Surface  ({datetime.date.today()})")
    ax.view_init(elev=26, azim=-128)
    fig.colorbar(surf, shrink=0.5, pad=0.1, label="IV %")
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "vol_surface.png"), dpi=130)
    plt.close()


def plot_skew(df):
    target = 30 / 365.0
    T0 = min(df["T"].unique(), key=lambda t: abs(t - target))
    sub = df[df["T"] == T0].sort_values("moneyness")
    plt.figure(figsize=(9, 5))
    plt.plot(sub["moneyness"], sub["iv"] * 100, "o-", color="#2563eb")
    plt.axvline(1.0, ls="--", color="gray", label="at-the-money")
    plt.xlabel("Moneyness (K/S)")
    plt.ylabel("Implied vol (%)")
    plt.title(f"{TICKER} Volatility Skew (~{T0*365:.0f}-day expiry)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "vol_skew.png"), dpi=130)
    plt.close()


def plot_term(df):
    rows = []
    for T0 in sorted(df["T"].unique()):
        sub = df[df["T"] == T0]
        idx = (sub["moneyness"] - 1.0).abs().idxmin()
        rows.append((T0 * 365, sub.loc[idx, "iv"] * 100))
    if len(rows) < 2:
        return
    days, ivs = zip(*rows)
    plt.figure(figsize=(9, 5))
    plt.plot(days, ivs, "o-", color="#7c3aed")
    plt.xlabel("Days to expiry")
    plt.ylabel("ATM implied vol (%)")
    plt.title(f"{TICKER} ATM Volatility Term Structure")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "term_structure.png"), dpi=130)
    plt.close()


def plot_svi(df, S):
    target = 30 / 365.0
    T0 = min(df["T"].unique(), key=lambda t: abs(t - target))
    sub = df[df["T"] == T0]
    k = np.log(sub["moneyness"].values)
    w = (sub["iv"].values ** 2) * T0
    params, rmse = calibrate_svi(k, w)
    kk = np.linspace(k.min(), k.max(), 200)
    iv_fit = np.sqrt(np.maximum(svi_total_variance(kk, **params), 1e-10) / T0) * 100
    g = butterfly_g(kk, params)
    plt.figure(figsize=(9, 5))
    plt.scatter(k, sub["iv"].values * 100, s=22, color="#2563eb", label="market IV")
    plt.plot(kk, iv_fit, color="#dc2626", lw=2, label="SVI fit")
    plt.axvline(0.0, ls="--", color="gray")
    plt.xlabel("log-moneyness  log(K/S)")
    plt.ylabel("Implied vol (%)")
    plt.title(f"SVI calibration, ~{T0*365:.0f}-day slice "
              f"(RMSE {rmse:.4f}, min g(k) {g.min():+.3f})")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "svi_fit.png"), dpi=130)
    plt.close()
    return rmse, float(g.min())


def vrp_analysis():
    spy, vix = get_vix_spy(years=12)
    rets = spy.pct_change()
    # forward realized vol over the next 21 trading days, annualized (%)
    fwd_rv = rets.rolling(21).std().shift(-21) * np.sqrt(252) * 100
    df = pd.DataFrame({"VIX": vix, "fwd_RV": fwd_rv}).dropna()
    df["VRP"] = df["VIX"] - df["fwd_RV"]

    plt.figure(figsize=(11, 5))
    plt.plot(df.index, df["VIX"], lw=1.0, color="#dc2626", label="VIX (30d implied)")
    plt.plot(df.index, df["fwd_RV"], lw=1.0, alpha=0.8, color="#2563eb",
             label="Realized vol (next 21d)")
    plt.ylabel("Annualized vol (%)")
    plt.title("Implied (VIX) vs subsequent Realized Volatility — the variance risk premium")
    plt.legend(loc="upper right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "vrp.png"), dpi=130)
    plt.close()
    return df["VRP"].mean(), (df["VRP"] > 0).mean() * 100, df


def main():
    print(f"Fetching {TICKER} spot, rate, and option chains...")
    S = get_spot(TICKER)
    r = get_riskfree()
    chains = get_chains(TICKER, max_expiries=12)
    if chains.empty:
        print("No option chain data returned (market data unavailable). Try again.")
        return
    surf = build_surface(chains, S, r)
    print(f"Spot ${S:,.2f} | risk-free {r*100:.2f}% | "
          f"{len(surf)} valid IV points across {surf['T'].nunique()} expiries")

    plot_surface(surf, S)
    plot_skew(surf)
    plot_term(surf)
    svi_rmse, min_g = plot_svi(surf, S)

    # snapshot ATM ~30d IV
    target = 30 / 365.0
    T0 = min(surf["T"].unique(), key=lambda t: abs(t - target))
    sub = surf[surf["T"] == T0]
    atm_iv = sub.loc[(sub["moneyness"] - 1.0).abs().idxmin(), "iv"] * 100

    print("\nRunning variance-risk-premium analysis (VIX vs forward realized)...")
    mean_vrp, pct_pos, _ = vrp_analysis()

    print("\n=== FINDINGS ===")
    print(f"ATM ~{T0*365:.0f}d implied vol:        {atm_iv:.1f}%")
    print(f"Mean variance risk premium (12y):  {mean_vrp:+.2f} vol points")
    print(f"% of days implied > realized:      {pct_pos:.1f}%")
    print(f"SVI fit (~30d slice):              RMSE {svi_rmse:.4f}, "
          f"butterfly min g(k) = {min_g:+.3f} "
          f"({'no-arb' if min_g >= 0 else 'butterfly arb present'})")
    print("\nInterpretation: implied vol sits above subsequent realized vol the "
          "large majority of the time — the variance risk premium. Selling vol "
          "harvests it, but the left tail (when realized spikes above implied) is "
          "where vol sellers blow up. Honest, not a free lunch.")
    print("\nWrote: vol_surface.png, vol_skew.png, term_structure.png, vrp.png")


if __name__ == "__main__":
    main()
