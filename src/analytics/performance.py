import logging
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)

CYCLE_MAIN = 2
STEPS_CHG  = [5.0, 6.0, 7.0]
STEPS_DCHG = [9.0, 10.0]


@dataclass
class PerformanceSummary:
    chg_capacity_Ah:          float
    dchg_capacity_Ah:         float
    chg_energy_Wh:            float
    dchg_energy_Wh:           float
    coulombic_efficiency_pct: float
    energy_efficiency_pct:    float
    chg_mid_volt_V:           float
    dchg_mid_volt_V:          float
    chg_time_h:               float
    dchg_time_h:              float
    avg_chg_power_W:          float
    avg_dchg_power_W:         float
    peak_chg_current_A:       float
    peak_dchg_current_A:      float
    peak_pack_voltage_V:      float
    min_pack_voltage_V:       float
    chg_c_rate:               float
    dchg_c_rate:              float
    nominal_capacity_Ah:      float


class PerformanceAnalytics:
    def __init__(self, cycle_df, record_df):
        self.cycle_df  = cycle_df
        self.record_df = record_df

    def compute(self):
        logger.info("Computing performance analytics …")
        cyc = self.cycle_df[self.cycle_df["cycle"] == CYCLE_MAIN]
        if cyc.empty:
            raise ValueError("Cycle 2 not found in Cycle Layer.")
        row = cyc.iloc[0]

        chg_cap  = float(row["chg_capacity_Ah"])
        dchg_cap = float(row["dchg_capacity_Ah"])
        chg_e    = float(row["chg_energy_Wh"])
        dchg_e   = float(row["dchg_energy_Wh"])
        ce       = float(row["coulombic_efficiency_pct"])
        ee       = float(row["energy_efficiency_pct"])
        chg_t_h  = float(row["chg_time_s"]) / 3600.0
        dchg_t_h = float(row["dchg_time_s"]) / 3600.0
        chg_mid  = float(row["chg_mid_volt_V"])
        dchg_mid = float(row["dchg_mid_volt_V"])

        c2   = self.record_df[self.record_df["cycle_id"] == CYCLE_MAIN]
        chg  = c2[c2["step_id"].isin(STEPS_CHG)]
        dchg = c2[c2["step_id"].isin(STEPS_DCHG)]

        avg_chg_pw  = float(chg["power_W"].abs().mean())   if not chg.empty  else 0.0
        avg_dchg_pw = float(dchg["power_W"].abs().mean())  if not dchg.empty else 0.0
        pk_chg_I    = float(chg["current_A"].max())        if not chg.empty  else 0.0
        pk_dchg_I   = float(dchg["current_A"].abs().max()) if not dchg.empty else 0.0
        peak_V      = float(chg["voltage_V"].max())        if not chg.empty  else 0.0
        min_V       = float(dchg["voltage_V"].min())       if not dchg.empty else 0.0

        nominal = dchg_cap if dchg_cap > 0 else 1.0
        ps = PerformanceSummary(
            chg_capacity_Ah=chg_cap,
            dchg_capacity_Ah=dchg_cap,
            chg_energy_Wh=chg_e,
            dchg_energy_Wh=dchg_e,
            coulombic_efficiency_pct=ce,
            energy_efficiency_pct=ee,
            chg_mid_volt_V=chg_mid,
            dchg_mid_volt_V=dchg_mid,
            chg_time_h=chg_t_h,
            dchg_time_h=dchg_t_h,
            avg_chg_power_W=avg_chg_pw,
            avg_dchg_power_W=avg_dchg_pw,
            peak_chg_current_A=pk_chg_I,
            peak_dchg_current_A=pk_dchg_I,
            peak_pack_voltage_V=peak_V,
            min_pack_voltage_V=min_V,
            chg_c_rate=pk_chg_I / nominal,
            dchg_c_rate=pk_dchg_I / nominal,
            nominal_capacity_Ah=nominal,
        )
        logger.info(
            "Performance | CE=%.3f%% EE=%.3f%% chg=%.3fAh dchg=%.3fAh",
            ce, ee, chg_cap, dchg_cap,
        )
        return ps

    def summary_text(self, ps):
        lines = [
            "=" * 56, "PERFORMANCE SUMMARY", "=" * 56,
            f"  Charge Capacity        : {ps.chg_capacity_Ah:.3f} Ah",
            f"  Discharge Capacity     : {ps.dchg_capacity_Ah:.3f} Ah",
            f"  Charge Energy          : {ps.chg_energy_Wh:.1f} Wh",
            f"  Discharge Energy       : {ps.dchg_energy_Wh:.1f} Wh",
            f"  Coulombic Efficiency   : {ps.coulombic_efficiency_pct:.3f} %",
            f"  Energy Efficiency      : {ps.energy_efficiency_pct:.3f} %",
            f"  Charge Mid-Voltage     : {ps.chg_mid_volt_V:.3f} V",
            f"  Discharge Mid-Voltage  : {ps.dchg_mid_volt_V:.3f} V",
            f"  Charge Duration        : {ps.chg_time_h:.2f} h",
            f"  Discharge Duration     : {ps.dchg_time_h:.2f} h",
            f"  Peak Charge Current    : {ps.peak_chg_current_A:.1f} A ({ps.chg_c_rate:.2f}C)",
            f"  Peak Discharge Current : {ps.peak_dchg_current_A:.1f} A ({ps.dchg_c_rate:.2f}C)",
            f"  Avg Charge Power       : {ps.avg_chg_power_W:.1f} W",
            f"  Avg Discharge Power    : {ps.avg_dchg_power_W:.1f} W",
            f"  Peak Pack Voltage      : {ps.peak_pack_voltage_V:.3f} V",
            f"  Min Pack Voltage       : {ps.min_pack_voltage_V:.3f} V",
            "=" * 56,
        ]
        return "\n".join(lines)