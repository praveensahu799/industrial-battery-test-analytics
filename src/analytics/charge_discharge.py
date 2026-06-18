import logging
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)

CYCLE_MAIN = 2
STEPS_CC   = [5.0, 6.0]
STEPS_CV   = [7.0]
STEPS_CHG  = [5.0, 6.0, 7.0]
STEPS_DCHG = [9.0, 10.0]
STEPS_R8   = [8.0]
STEPS_R11  = [11.0]
STEPS_ALL  = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]


@dataclass
class ChargeDischargeSummary:
    chg_start_volt_V:      float
    chg_end_volt_V:        float
    chg_peak_power_W:      float
    chg_cc_duration_h:     float
    chg_cv_duration_h:     float
    chg_mid_volt_V:        float
    dchg_start_volt_V:     float
    dchg_end_volt_V:       float
    dchg_peak_power_W:     float
    dchg_avg_power_W:      float
    dchg_mid_volt_V:       float
    rest_post_chg_volt_V:  float
    rest_post_dchg_volt_V: float
    voltage_hysteresis_V:  float


class ChargeDischargAnalytics:
    def __init__(self, record_df, cycle_df):
        c2 = record_df[record_df["cycle_id"] == CYCLE_MAIN].copy()
        self._chg      = c2[c2["step_id"].isin(STEPS_CHG)]
        self._dchg     = c2[c2["step_id"].isin(STEPS_DCHG)]
        self._cc       = c2[c2["step_id"].isin(STEPS_CC)]
        self._cv       = c2[c2["step_id"].isin(STEPS_CV)]
        self._r8       = c2[c2["step_id"].isin(STEPS_R8)]
        self._r11      = c2[c2["step_id"].isin(STEPS_R11)]
        self._c2       = c2
        self._cycle_df = cycle_df

    def compute(self):
        logger.info("Computing charge-discharge analytics …")
        chg  = self._chg
        dchg = self._dchg

        def dur_h(df):
            if df.empty:
                return 0.0
            return (df["elapsed_s"].max() - df["elapsed_s"].min()) / 3600.0

        cyc2     = self._cycle_df[self._cycle_df["cycle"] == CYCLE_MAIN]
        chg_mid  = float(cyc2["chg_mid_volt_V"].iloc[0])  if not cyc2.empty else 0.0
        dchg_mid = float(cyc2["dchg_mid_volt_V"].iloc[0]) if not cyc2.empty else 0.0

        return ChargeDischargeSummary(
            chg_start_volt_V=float(chg["voltage_V"].iloc[0])     if not chg.empty  else 0.0,
            chg_end_volt_V=float(chg["voltage_V"].iloc[-1])      if not chg.empty  else 0.0,
            chg_peak_power_W=float(chg["power_W"].max())         if not chg.empty  else 0.0,
            chg_cc_duration_h=dur_h(self._cc),
            chg_cv_duration_h=dur_h(self._cv),
            chg_mid_volt_V=chg_mid,
            dchg_start_volt_V=float(dchg["voltage_V"].iloc[0])   if not dchg.empty else 0.0,
            dchg_end_volt_V=float(dchg["voltage_V"].iloc[-1])    if not dchg.empty else 0.0,
            dchg_peak_power_W=float(dchg["power_W"].abs().max())  if not dchg.empty else 0.0,
            dchg_avg_power_W=float(dchg["power_W"].abs().mean())  if not dchg.empty else 0.0,
            dchg_mid_volt_V=dchg_mid,
            rest_post_chg_volt_V=float(self._r8["voltage_V"].mean())   if not self._r8.empty  else 0.0,
            rest_post_dchg_volt_V=float(self._r11["voltage_V"].mean()) if not self._r11.empty else 0.0,
            voltage_hysteresis_V=chg_mid - dchg_mid,
        )

    def get_c2_main(self):
        return self._c2[self._c2["step_id"].isin(STEPS_ALL)].copy()

    def summary_text(self, s):
        lines = [
            "=" * 56, "CHARGE-DISCHARGE PROFILE", "=" * 56,
            f"  Chg start V      : {s.chg_start_volt_V:.3f} V",
            f"  Chg end V        : {s.chg_end_volt_V:.3f} V",
            f"  Chg peak power   : {s.chg_peak_power_W:.1f} W",
            f"  CC duration      : {s.chg_cc_duration_h:.2f} h",
            f"  CV duration      : {s.chg_cv_duration_h:.2f} h",
            f"  Chg mid-volt     : {s.chg_mid_volt_V:.3f} V",
            f"  Dchg start V     : {s.dchg_start_volt_V:.3f} V",
            f"  Dchg end V       : {s.dchg_end_volt_V:.3f} V",
            f"  Dchg peak power  : {s.dchg_peak_power_W:.1f} W",
            f"  Dchg avg power   : {s.dchg_avg_power_W:.1f} W",
            f"  Dchg mid-volt    : {s.dchg_mid_volt_V:.3f} V",
            f"  Rest post-chg V  : {s.rest_post_chg_volt_V:.3f} V",
            f"  Rest post-dchg V : {s.rest_post_dchg_volt_V:.3f} V",
            f"  Hysteresis       : {s.voltage_hysteresis_V:.3f} V",
            "=" * 56,
        ]
        return "\n".join(lines)