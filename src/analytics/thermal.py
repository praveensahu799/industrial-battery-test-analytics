import logging
from dataclasses import dataclass, field
import pandas as pd

logger = logging.getLogger(__name__)

CYCLE_MAIN = 2
STEPS_CHG  = [5.0, 6.0, 7.0]
STEPS_DCHG = [9.0, 10.0]
STEPS_REST = [8.0, 11.0]
STEPS_MAIN = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
THERM_COLS = ["thermistor1_C", "thermistor2_C", "thermistor3_C", "thermistor4_C"]
HOTSPOT_C  = 45.0
SPREAD_C   = 5.0


@dataclass
class ThermalSummary:
    global_max_C:       float
    global_min_C:       float
    global_avg_C:       float
    global_std_C:       float
    therm_avg:          dict
    therm_max:          dict
    therm_min:          dict
    avg_spread_C:       float
    max_spread_C:       float
    bms_max_temp_avg_C: float
    bms_min_temp_avg_C: float
    chg_avg_temp_C:     float
    dchg_avg_temp_C:    float
    rest_avg_temp_C:    float
    hotspot_flag:       bool
    spread_flag:        bool
    temp_df:            pd.DataFrame = field(default_factory=pd.DataFrame)


class ThermalAnalytics:
    def __init__(self, record_df):
        self._c2 = record_df[
            (record_df["cycle_id"] == CYCLE_MAIN) &
            (record_df["step_id"].isin(STEPS_MAIN))
        ].copy()

    def compute(self):
        logger.info("Computing thermal analytics …")
        c2    = self._c2
        avail = [col for col in THERM_COLS if col in c2.columns]
        tdf   = c2[avail].apply(pd.to_numeric, errors="coerce")
        all_t = tdf.stack().dropna()
        spread = (tdf.max(axis=1) - tdf.min(axis=1)).dropna()

        def phase_avg(steps):
            sub = c2[c2["step_id"].isin(steps)]
            if sub.empty or not avail:
                return 0.0
            return float(sub[avail].apply(pd.to_numeric, errors="coerce").mean().mean())

        bms_max = float(pd.to_numeric(c2["max_cell_temp_C"], errors="coerce").mean()) \
                  if "max_cell_temp_C" in c2.columns else 0.0
        bms_min = float(pd.to_numeric(c2["min_cell_temp_C"], errors="coerce").mean()) \
                  if "min_cell_temp_C" in c2.columns else 0.0

        return ThermalSummary(
            global_max_C=float(all_t.max()),
            global_min_C=float(all_t.min()),
            global_avg_C=float(all_t.mean()),
            global_std_C=float(all_t.std()),
            therm_avg=tdf.mean().to_dict(),
            therm_max=tdf.max().to_dict(),
            therm_min=tdf.min().to_dict(),
            avg_spread_C=float(spread.mean()),
            max_spread_C=float(spread.max()),
            bms_max_temp_avg_C=bms_max,
            bms_min_temp_avg_C=bms_min,
            chg_avg_temp_C=phase_avg(STEPS_CHG),
            dchg_avg_temp_C=phase_avg(STEPS_DCHG),
            rest_avg_temp_C=phase_avg(STEPS_REST),
            hotspot_flag=(float(all_t.max()) >= HOTSPOT_C),
            spread_flag=(float(spread.max()) > SPREAD_C),
            temp_df=tdf,
        )

    def summary_text(self, s):
        lines = [
            "=" * 56, "THERMAL ANALYTICS", "=" * 56,
            f"  Peak temp    : {s.global_max_C:.1f} °C",
            f"  Min temp     : {s.global_min_C:.1f} °C",
            f"  Avg temp     : {s.global_avg_C:.1f} °C",
            f"  Avg spread   : {s.avg_spread_C:.2f} °C",
            f"  Max spread   : {s.max_spread_C:.2f} °C",
            f"  Chg avg      : {s.chg_avg_temp_C:.1f} °C",
            f"  Dchg avg     : {s.dchg_avg_temp_C:.1f} °C",
            f"  Rest avg     : {s.rest_avg_temp_C:.1f} °C",
            f"  Hotspot      : {'YES' if s.hotspot_flag else 'NO'}",
            f"  Spread flag  : {'YES' if s.spread_flag else 'NO'}",
            "=" * 56,
        ]
        return "\n".join(lines)