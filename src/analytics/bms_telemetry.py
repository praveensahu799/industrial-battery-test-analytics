import logging
from dataclasses import dataclass, field
import pandas as pd

logger = logging.getLogger(__name__)

CYCLE_MAIN   = 2
STEPS_MAIN   = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
BMS_ACTIVE_V = 40.0


@dataclass
class BMSTelemetrySummary:
    soc_start_pct:           float
    soc_end_pct:             float
    soc_min_pct:             float
    soc_max_pct:             float
    residual_cap_max_Ah:     float
    residual_cap_start_Ah:   float
    residual_cap_end_Ah:     float
    bms_volt_avg_V:          float
    cycler_volt_avg_V:       float
    volt_discrepancy_avg_mV: float
    bms_curr_avg_A:          float
    cycler_curr_avg_A:       float
    curr_discrepancy_avg_A:  float
    bms_cycle_count_start:   int
    bms_cycle_count_end:     int
    bms_life_avg:            float
    c2_df:                   pd.DataFrame = field(default_factory=pd.DataFrame)


class BMSTelemetryAnalytics:
    def __init__(self, record_df):
        self._c2m = record_df[
            (record_df["cycle_id"] == CYCLE_MAIN) &
            (record_df["step_id"].isin(STEPS_MAIN))
        ].copy()

    def compute(self):
        logger.info("Computing BMS telemetry analytics …")
        df = self._c2m

        def n(col):
            if col not in df.columns:
                return pd.Series(dtype=float)
            return pd.to_numeric(df[col], errors="coerce")

        soc   = n("soc_pct").dropna()
        res   = n("residual_cap_Ah").dropna()
        bms_v = n("bms_voltage_V")
        cyc_v = n("voltage_V")
        valid = (bms_v > BMS_ACTIVE_V) & cyc_v.notna()
        bv_avg = float(bms_v[valid].mean()) if valid.any() else 0.0
        cv_avg = float(cyc_v[valid].mean()) if valid.any() else 0.0

        bms_i = n("bms_current_A").dropna()
        cyc_i = n("current_A").dropna()
        cycs  = n("bms_cycle_count").dropna()
        life  = n("bms_life").dropna()

        bms_i_avg = float(bms_i.mean()) if not bms_i.empty else 0.0
        cyc_i_avg = float(cyc_i.mean()) if not cyc_i.empty else 0.0

        return BMSTelemetrySummary(
            soc_start_pct=float(soc.iloc[0])   if not soc.empty else 0.0,
            soc_end_pct=float(soc.iloc[-1])     if not soc.empty else 0.0,
            soc_min_pct=float(soc.min())        if not soc.empty else 0.0,
            soc_max_pct=float(soc.max())        if not soc.empty else 0.0,
            residual_cap_max_Ah=float(res.max())    if not res.empty else 0.0,
            residual_cap_start_Ah=float(res.iloc[0]) if not res.empty else 0.0,
            residual_cap_end_Ah=float(res.iloc[-1])  if not res.empty else 0.0,
            bms_volt_avg_V=bv_avg,
            cycler_volt_avg_V=cv_avg,
            volt_discrepancy_avg_mV=(bv_avg - cv_avg) * 1000.0,
            bms_curr_avg_A=bms_i_avg,
            cycler_curr_avg_A=cyc_i_avg,
            curr_discrepancy_avg_A=bms_i_avg - cyc_i_avg,
            bms_cycle_count_start=int(cycs.iloc[0])  if not cycs.empty else 0,
            bms_cycle_count_end=int(cycs.iloc[-1])    if not cycs.empty else 0,
            bms_life_avg=float(life.mean()) if not life.empty else 0.0,
            c2_df=df,
        )

    def summary_text(self, s):
        lines = [
            "=" * 56, "BMS TELEMETRY ANALYTICS", "=" * 56,
            f"  SOC start/end       : {s.soc_start_pct:.1f}% / {s.soc_end_pct:.1f}%",
            f"  SOC range           : {s.soc_min_pct:.1f}% – {s.soc_max_pct:.1f}%",
            f"  Residual cap max    : {s.residual_cap_max_Ah:.3f} Ah",
            f"  Residual cap start  : {s.residual_cap_start_Ah:.3f} Ah",
            f"  Residual cap end    : {s.residual_cap_end_Ah:.3f} Ah",
            f"  BMS volt avg        : {s.bms_volt_avg_V:.3f} V",
            f"  Cycler volt avg     : {s.cycler_volt_avg_V:.3f} V",
            f"  Volt discrepancy    : {s.volt_discrepancy_avg_mV:+.1f} mV",
            f"  BMS cycle count     : {s.bms_cycle_count_start} → {s.bms_cycle_count_end}",
            "=" * 56,
        ]
        return "\n".join(lines)