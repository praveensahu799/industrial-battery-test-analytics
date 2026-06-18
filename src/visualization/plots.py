import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

CYCLE_MAIN = 2
STEPS_CHG  = [5.0, 6.0, 7.0]
STEPS_DCHG = [9.0, 10.0]
STEPS_REST = [8.0, 11.0]
STEPS_ALL  = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]

CELL_PAL = list(plt.cm.tab20.colors)

STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor":   "#F8F8F8",
    "axes.edgecolor":   "#CCCCCC",
    "axes.grid":        True,
    "grid.color":       "#DDDDDD",
    "grid.linestyle":   "--",
    "grid.alpha":       0.7,
    "font.family":      "DejaVu Sans",
    "font.size":        10,
    "axes.titlesize":   11,
    "axes.labelsize":   10,
    "xtick.labelsize":  9,
    "ytick.labelsize":  9,
    "lines.linewidth":  1.4,
    "legend.frameon":   True,
    "legend.framealpha": 0.9,
    "legend.fontsize":  9,
}

C = {
    "chg":  "#2E86AB",
    "dchg": "#E84855",
    "rest": "#4CAF50",
    "volt": "#1565C0",
    "curr": "#C62828",
    "pwr":  "#6A1B9A",
    "soc":  "#00695C",
    "temp": "#E65100",
    "cell": "#3F51B5",
    "bms":  "#FF6F00",
    "grey": "#546E7A",
}


def _st():
    plt.rcParams.update(STYLE)


def _save(fig, path):
    fig.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _c2df(record_df):
    df = record_df[
        (record_df["cycle_id"] == CYCLE_MAIN) &
        (record_df["step_id"].isin(STEPS_ALL))
    ].copy()
    t0 = df["elapsed_s"].min()
    df["test_h"] = (df["elapsed_s"] - t0) / 3600.0
    return df


def plot_voltage_current_profile(record_df, out_dir):
    _st()
    df   = _c2df(record_df)
    chg  = df["step_id"].isin(STEPS_CHG)
    dchg = df["step_id"].isin(STEPS_DCHG)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    fig.suptitle("Pack Voltage & Current Profile  (Cycle 2)", fontsize=13, fontweight="bold")

    ax1.plot(df["test_h"], df["voltage_V"], color=C["volt"], lw=1.2, label="Voltage")
    ax1.fill_between(df["test_h"], 40, 66, where=chg,  alpha=0.05, color=C["chg"],  step="post")
    ax1.fill_between(df["test_h"], 40, 66, where=dchg, alpha=0.05, color=C["dchg"], step="post")
    ax1.set_ylabel("Voltage (V)")
    ax1.legend(loc="lower right")

    ax2.plot(df["test_h"], df["current_A"], color=C["curr"], lw=1.0)
    ax2.fill_between(df["test_h"], df["current_A"],
                     where=(df["current_A"] > 0), alpha=0.25, color=C["chg"],  label="Charge")
    ax2.fill_between(df["test_h"], df["current_A"],
                     where=(df["current_A"] < 0), alpha=0.25, color=C["dchg"], label="Discharge")
    ax2.axhline(0, color="#AAAAAA", lw=0.8)
    ax2.set_ylabel("Current (A)")
    ax2.set_xlabel("Elapsed Time (h)")
    ax2.legend()

    fig.tight_layout()
    return _save(fig, Path(out_dir) / "01_voltage_current_profile.png")


def plot_power_profile(record_df, out_dir):
    _st()
    df = _c2df(record_df)

    fig, ax = plt.subplots(figsize=(12, 4))
    fig.suptitle("Pack Power Profile  (Cycle 2)", fontsize=13, fontweight="bold")

    ax.fill_between(df["test_h"], df["power_W"],
                    where=(df["power_W"] >= 0), alpha=0.45, color=C["chg"],  label="Charge (+W)")
    ax.fill_between(df["test_h"], df["power_W"],
                    where=(df["power_W"] < 0),  alpha=0.45, color=C["dchg"], label="Discharge (-W)")
    ax.plot(df["test_h"], df["power_W"], color="#444444", lw=0.5)
    ax.axhline(0, color="#AAAAAA", lw=0.8)
    ax.set_xlabel("Elapsed Time (h)")
    ax.set_ylabel("Power (W)")
    ax.legend()

    fig.tight_layout()
    return _save(fig, Path(out_dir) / "02_power_profile.png")


def plot_capacity_energy_progression(record_df, out_dir):
    _st()
    df   = _c2df(record_df)
    chg  = df["step_id"].isin(STEPS_CHG)
    dchg = df["step_id"].isin(STEPS_DCHG)
    rest = df["step_id"].isin(STEPS_REST)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    fig.suptitle("Cumulative Capacity & Energy  (Cycle 2)", fontsize=13, fontweight="bold")

    ax1.plot(df["test_h"][chg],  df["cum_cap_Ah"][chg],  color=C["chg"],  lw=1.6, label="Charge")
    ax1.plot(df["test_h"][rest], df["cum_cap_Ah"][rest],  color=C["rest"], lw=1.2, label="Rest")
    ax1.plot(df["test_h"][dchg], df["cum_cap_Ah"][dchg],  color=C["dchg"], lw=1.6, label="Discharge")
    ax1.set_ylabel("Cumulative Capacity (Ah)")
    ax1.set_ylim(-5, 125)
    ax1.legend()

    ax2.plot(df["test_h"][chg],  df["cum_eng_Wh"][chg],  color=C["chg"],  lw=1.6, label="Charge")
    ax2.plot(df["test_h"][rest], df["cum_eng_Wh"][rest],  color=C["rest"], lw=1.2, label="Rest")
    ax2.plot(df["test_h"][dchg], df["cum_eng_Wh"][dchg],  color=C["dchg"], lw=1.6, label="Discharge")
    ax2.set_ylabel("Cumulative Energy (Wh)")
    ax2.set_xlabel("Elapsed Time (h)")
    ax2.legend()

    fig.tight_layout()
    return _save(fig, Path(out_dir) / "03_capacity_energy.png")


def plot_cell_voltages_over_time(cell_df, record_df, out_dir):
    _st()
    main = _c2df(record_df)
    idx  = cell_df.index.intersection(main.index)
    t    = main.loc[idx, "test_h"]
    cdf  = cell_df.loc[idx]

    fig, ax = plt.subplots(figsize=(13, 5))
    fig.suptitle("Individual Cell Voltages Over Time  (Cycle 2)", fontsize=13, fontweight="bold")

    for i, col in enumerate(cdf.columns):
        ax.plot(t, cdf[col], lw=0.8, color=CELL_PAL[i % 20],
                label=f"Cell {i + 1}", alpha=0.85)

    ax.set_xlabel("Elapsed Time (h)")
    ax.set_ylabel("Cell Voltage (V)")
    ax.legend(ncol=4, fontsize=7, loc="upper right")
    fig.tight_layout()
    return _save(fig, Path(out_dir) / "04_cell_voltages_time.png")


def plot_cell_voltage_spread(spread_series, record_df, out_dir):
    _st()
    main = _c2df(record_df)
    idx  = spread_series.index.intersection(main.index)
    t    = main.loc[idx, "test_h"]
    sp   = spread_series.loc[idx]

    fig, ax = plt.subplots(figsize=(12, 4))
    fig.suptitle("Cell Voltage Spread (Max-Min)  (Cycle 2)", fontsize=13, fontweight="bold")

    ax.plot(t, sp * 1000, color=C["cell"], lw=0.9)
    ax.fill_between(t, sp * 1000, alpha=0.2, color=C["cell"])
    ax.axhline(50, color=C["dchg"], lw=1.2, ls="--", label="50 mV threshold")
    ax.set_xlabel("Elapsed Time (h)")
    ax.set_ylabel("Spread (mV)")
    ax.set_ylim(bottom=0)
    ax.legend()

    fig.tight_layout()
    return _save(fig, Path(out_dir) / "05_cell_voltage_spread.png")


def plot_cell_avg_bar(cell_avg, out_dir):
    _st()
    cells  = sorted(cell_avg.keys(), key=lambda x: int(x.replace("cell", "").replace("_V", "")))
    avgs   = [cell_avg[c] for c in cells]
    labels = [c.replace("_V", "") for c in cells]
    overall = float(np.mean(avgs))

    fig, ax = plt.subplots(figsize=(12, 4))
    fig.suptitle("Per-Cell Average Voltage  (Cycle 2)", fontsize=13, fontweight="bold")

    ax.bar(labels, avgs, color=C["cell"], alpha=0.82, edgecolor="white")
    ax.axhline(overall, color=C["dchg"], lw=1.4, ls="--",
               label=f"Pack avg: {overall:.4f} V")
    ax.set_xlabel("Cell")
    ax.set_ylabel("Average Voltage (V)")
    ax.legend()
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.3f"))

    yr = max(avgs) - min(avgs)
    mg = max(yr * 3, 0.004)
    ax.set_ylim(min(avgs) - mg, max(avgs) + mg)

    fig.tight_layout()
    return _save(fig, Path(out_dir) / "06_cell_avg_bar.png")


def plot_temperature_profiles(temp_df, record_df, out_dir):
    _st()
    main = _c2df(record_df)
    idx  = temp_df.index.intersection(main.index)
    t    = main.loc[idx, "test_h"]
    tdf  = temp_df.loc[idx]

    fig, ax = plt.subplots(figsize=(12, 4))
    fig.suptitle("Thermistor Temperature Profiles  (Cycle 2)", fontsize=13, fontweight="bold")

    clrs = ["#E65100", "#1565C0", "#2E7D32", "#6A1B9A"]
    for i, col in enumerate(tdf.columns):
        lbl = col.replace("thermistor", "T").replace("_C", "")
        ax.plot(t, tdf[col], lw=1.2, color=clrs[i % 4], label=lbl)

    ax.axhline(45, color=C["dchg"], lw=1.0, ls="--", alpha=0.7, label="45°C")
    ax.set_xlabel("Elapsed Time (h)")
    ax.set_ylabel("Temperature (°C)")
    ax.set_ylim(20, 50)
    ax.legend(ncol=3)

    fig.tight_layout()
    return _save(fig, Path(out_dir) / "07_temperature_profiles.png")


def plot_thermal_spread(temp_df, record_df, out_dir):
    _st()
    main   = _c2df(record_df)
    idx    = temp_df.index.intersection(main.index)
    t      = main.loc[idx, "test_h"]
    spread = temp_df.loc[idx].max(axis=1) - temp_df.loc[idx].min(axis=1)

    fig, ax = plt.subplots(figsize=(12, 3))
    fig.suptitle("Thermal Spread (Max-Min Thermistor)  (Cycle 2)", fontsize=13, fontweight="bold")

    ax.fill_between(t, spread, alpha=0.4, color=C["temp"])
    ax.plot(t, spread, color=C["temp"], lw=0.9)
    ax.axhline(5, color=C["dchg"], lw=1.2, ls="--", label="5°C threshold")
    ax.set_xlabel("Elapsed Time (h)")
    ax.set_ylabel("Spread (°C)")
    ax.set_ylim(bottom=0)
    ax.legend()

    fig.tight_layout()
    return _save(fig, Path(out_dir) / "08_thermal_spread.png")


def plot_soc_profile(record_df, out_dir):
    _st()
    df   = _c2df(record_df)
    soc  = pd.to_numeric(df["soc_pct"], errors="coerce")
    chg  = df["step_id"].isin(STEPS_CHG)
    dchg = df["step_id"].isin(STEPS_DCHG)

    fig, ax = plt.subplots(figsize=(12, 3.5))
    fig.suptitle("BMS State of Charge (SOC)  (Cycle 2)", fontsize=13, fontweight="bold")

    ax.fill_between(df["test_h"][chg],  soc[chg],  alpha=0.30, color=C["chg"])
    ax.fill_between(df["test_h"][dchg], soc[dchg], alpha=0.30, color=C["dchg"])
    ax.plot(df["test_h"], soc, color=C["soc"], lw=1.2)
    ax.set_xlabel("Elapsed Time (h)")
    ax.set_ylabel("SOC (%)")
    ax.set_ylim(-2, 105)
    ax.set_xlim(left=0)

    fig.tight_layout()
    return _save(fig, Path(out_dir) / "09_soc_profile.png")


def plot_bms_vs_cycler_voltage(record_df, out_dir):
    _st()
    df    = _c2df(record_df)
    bms_v = pd.to_numeric(df["bms_voltage_V"], errors="coerce")
    cyc_v = pd.to_numeric(df["voltage_V"],     errors="coerce")
    valid = (bms_v > 40) & cyc_v.notna()
    t     = df["test_h"][valid]
    bv    = bms_v[valid]
    cv    = cyc_v[valid]
    dmV   = (bv - cv) * 1000.0

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    fig.suptitle("BMS vs Cycler Voltage  (Cycle 2)", fontsize=13, fontweight="bold")

    ax1.plot(t, cv, color=C["volt"], lw=1.2, label="Cycler")
    ax1.plot(t, bv, color=C["bms"],  lw=1.0, ls="--", alpha=0.85, label="BMS")
    ax1.set_ylabel("Voltage (V)")
    ax1.legend()

    ax2.plot(t, dmV, color=C["grey"], lw=0.9)
    ax2.axhline(0,    color="#AAAAAA", lw=0.8)
    ax2.axhline(200,  color=C["dchg"], lw=0.8, ls="--", alpha=0.6, label="+200 mV")
    ax2.axhline(-200, color=C["dchg"], lw=0.8, ls="--", alpha=0.6, label="-200 mV")
    ax2.set_ylabel("BMS - Cycler (mV)")
    ax2.set_xlabel("Elapsed Time (h)")
    ax2.legend()

    fig.tight_layout()
    return _save(fig, Path(out_dir) / "10_bms_vs_cycler_voltage.png")


def plot_protection_flags(safety_summary, out_dir):
    _st()
    c2 = safety_summary.c2_df
    if c2.empty:
        fig, ax = plt.subplots(figsize=(9, 3))
        ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center")
        return _save(fig, Path(out_dir) / "11_protection_flags.png")

    t0 = c2["elapsed_s"].min()
    t  = (c2["elapsed_s"] - t0) / 3600.0

    triggered = {
        col: lbl
        for col, lbl in {
            "flag_ovp_l1":      "Cell OVP L1",
            "flag_uvp_l1":      "Cell UVP L1",
            "flag_uvp_l2":      "Cell UVP L2",
            "flag_pack_uvp_l1": "Pack UVP L1",
            "flag_soc_high_l1": "SOC High L1",
            "flag_soc_low_l2":  "SOC Low L2",
        }.items()
        if col in c2.columns
        and (pd.to_numeric(c2[col], errors="coerce") == 1).any()
    }

    bms_stat = pd.to_numeric(
        c2["bms_status"] if "bms_status" in c2.columns else pd.Series(0, index=c2.index),
        errors="coerce"
    ).fillna(0)

    n_panels = 1 + len(triggered)
    fig, axes = plt.subplots(
        n_panels, 1,
        figsize=(13, max(4, n_panels * 1.15)),
        sharex=True,
    )
    if n_panels == 1:
        axes = [axes]

    fig.suptitle("Protection Flag Activation Timeline  (Cycle 2)",
                 fontsize=13, fontweight="bold")

    axes[0].step(t, bms_stat, where="post", color=C["grey"], lw=1.0)
    axes[0].fill_between(t, bms_stat, step="post", alpha=0.4,
                         color=C["dchg"], where=(bms_stat > 0))
    axes[0].set_ylabel("BMS\nStatus", fontsize=8)
    axes[0].set_yticks([0, 1, 2, 10])
    axes[0].set_ylim(-0.5, 12)

    for ax, (col, lbl) in zip(axes[1:], triggered.items()):
        s = pd.to_numeric(c2[col], errors="coerce").fillna(0)
        ax.fill_between(t, s, step="post", alpha=0.6, color=C["dchg"])
        ax.step(t, s, where="post", color=C["curr"], lw=0.8)
        ax.set_ylabel(lbl, fontsize=8)
        ax.set_ylim(-0.1, 1.3)
        ax.set_yticks([0, 1])

    if not triggered:
        axes[0].text(0.5, 0.3, "No flags triggered in Cycle 2",
                     transform=axes[0].transAxes, ha="center", color=C["grey"])

    axes[-1].set_xlabel("Elapsed Time (h)")
    fig.tight_layout()
    return _save(fig, Path(out_dir) / "11_protection_flags.png")


def plot_mosfet_status(record_df, out_dir):
    _st()
    df   = _c2df(record_df)
    chgm = pd.to_numeric(df["chg_mos_status"],  errors="coerce").fillna(0)
    dchm = pd.to_numeric(df["dchg_mos_status"], errors="coerce").fillna(0)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 4), sharex=True)
    fig.suptitle("MOSFET Status Over Time  (Cycle 2)", fontsize=13, fontweight="bold")

    ax1.step(df["test_h"], chgm, where="post", color=C["chg"], lw=1.4)
    ax1.fill_between(df["test_h"], chgm, step="post", alpha=0.3, color=C["chg"])
    ax1.set_ylabel("Charge MOS\n(1=ON)")
    ax1.set_ylim(-0.1, 1.3)
    ax1.set_yticks([0, 1])

    ax2.step(df["test_h"], dchm, where="post", color=C["dchg"], lw=1.4)
    ax2.fill_between(df["test_h"], dchm, step="post", alpha=0.3, color=C["dchg"])
    ax2.set_ylabel("Dchg MOS\n(1=ON)")
    ax2.set_ylim(-0.1, 1.3)
    ax2.set_yticks([0, 1])
    ax2.set_xlabel("Elapsed Time (h)")

    fig.tight_layout()
    return _save(fig, Path(out_dir) / "12_mosfet_status.png")