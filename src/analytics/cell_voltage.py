import logging
from dataclasses import dataclass, field
import pandas as pd

logger = logging.getLogger(__name__)

CYCLE_MAIN = 2
STEPS_MAIN = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
CELL_COLS  = [f"cell{i}_V" for i in range(1, 17)]
IMBAL_MV   = 50.0


@dataclass
class CellVoltageSummary:
    cell_avg_V:      dict
    cell_min_V:      dict
    cell_max_V:      dict
    cell_std_V:      dict
    avg_spread_V:    float
    max_spread_V:    float
    min_spread_V:    float
    weakest_cell:    str
    strongest_cell:  str
    weakest_avg_V:   float
    strongest_avg_V: float
    imbalance_flag:  bool
    spread_series:   pd.Series    = field(default_factory=pd.Series)
    cell_df:         pd.DataFrame = field(default_factory=pd.DataFrame)


class CellVoltageAnalytics:
    def __init__(self, record_df):
        c2 = record_df[
            (record_df["cycle_id"] == CYCLE_MAIN) &
            (record_df["step_id"].isin(STEPS_MAIN))
        ].copy()
        avail = [c for c in CELL_COLS if c in c2.columns]
        self._cell_df = c2[avail].apply(pd.to_numeric, errors="coerce")
        self._c2      = c2

    def compute(self):
        logger.info("Computing cell voltage analytics …")
        df     = self._cell_df.dropna(how="all")
        spread = df.max(axis=1) - df.min(axis=1)
        avgs   = df.mean()
        return CellVoltageSummary(
            cell_avg_V=avgs.to_dict(),
            cell_min_V=df.min().to_dict(),
            cell_max_V=df.max().to_dict(),
            cell_std_V=df.std().to_dict(),
            avg_spread_V=float(spread.mean()),
            max_spread_V=float(spread.max()),
            min_spread_V=float(spread.min()),
            weakest_cell=str(avgs.idxmin()),
            strongest_cell=str(avgs.idxmax()),
            weakest_avg_V=float(avgs.min()),
            strongest_avg_V=float(avgs.max()),
            imbalance_flag=(float(spread.mean()) > IMBAL_MV / 1000.0),
            spread_series=spread,
            cell_df=df,
        )

    def summary_text(self, s):
        lines = [
            "=" * 56, "CELL VOLTAGE ANALYTICS", "=" * 56,
            f"  Cells analysed : {len(s.cell_avg_V)}",
            f"  Avg spread     : {s.avg_spread_V * 1000:.1f} mV",
            f"  Max spread     : {s.max_spread_V * 1000:.1f} mV",
            f"  Weakest cell   : {s.weakest_cell} ({s.weakest_avg_V:.4f} V)",
            f"  Strongest cell : {s.strongest_cell} ({s.strongest_avg_V:.4f} V)",
            f"  Imbalance      : {'YES' if s.imbalance_flag else 'NO'}",
            "=" * 56,
        ]
        return "\n".join(lines)