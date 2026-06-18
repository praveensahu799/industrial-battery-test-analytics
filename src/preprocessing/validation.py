import logging
import pandas as pd

logger = logging.getLogger(__name__)

BOUNDS = {
    "voltage_V":       (0.0,   70.0),
    "current_A":       (-60.0, 60.0),
    "power_W":         (-4000, 4000),
    "soc_pct":         (0.0,   100.0),
    "thermistor1_C":   (-10.0, 80.0),
    "thermistor2_C":   (-10.0, 80.0),
    "thermistor3_C":   (-10.0, 80.0),
    "thermistor4_C":   (-10.0, 80.0),
    "max_cell_volt_V": (2.0,   4.0),
    "min_cell_volt_V": (2.0,   4.0),
    "bms_voltage_V":   (0.0,   70.0),
    "residual_cap_Ah": (0.0,   200.0),
}


class DataQualityReport:
    def __init__(self):
        self.layer_summaries  = {}
        self.missing_pct      = {}
        self.duplicate_counts = {}
        self.out_of_range     = {}
        self.timestamp_issues = []
        self.warnings         = []
        self.overall_pass     = True


class DataValidationEngine:
    def __init__(self, layers):
        self.layers = layers
        self.report = DataQualityReport()

    def run(self):
        logger.info("Running data validation …")
        for name, df in self.layers.items():
            self._check_layer(name, df)
        self._check_timestamps()
        self._check_bounds()
        self._evaluate()
        logger.info("Validation complete. Pass=%s", self.report.overall_pass)
        return self.report

    def _check_layer(self, name, df):
        n    = max(len(df), 1)
        miss = (df.isnull().sum() / n * 100).round(2)
        miss = miss[miss > 0].to_dict()
        dups = int(df.duplicated().sum())
        if dups:
            self.report.warnings.append(f"{name}: {dups} duplicate row(s).")
        self.report.missing_pct[name]      = miss
        self.report.duplicate_counts[name] = dups
        self.report.layer_summaries[name]  = {
            "rows":            len(df),
            "columns":         df.shape[1],
            "duplicates":      dups,
            "missing_columns": len(miss),
        }

    def _check_timestamps(self):
        rec = self.layers.get("record")
        if rec is None or "system_time" not in rec.columns:
            return
        ts = rec["system_time"].dropna().sort_values()
        if ts.empty:
            self.report.timestamp_issues.append("No valid timestamps.")
            return
        dt  = ts.diff().dropna()
        neg = int((dt.dt.total_seconds() < 0).sum())
        if neg:
            msg = f"{neg} negative timestamp delta(s)."
            self.report.timestamp_issues.append(msg)
            self.report.warnings.append(msg)
        gaps = int((dt.dt.total_seconds() > 300).sum())
        if gaps:
            self.report.timestamp_issues.append(f"{gaps} gap(s) > 5 min.")
        if not self.report.timestamp_issues:
            self.report.timestamp_issues.append("Timestamps OK — monotonically increasing.")

    def _check_bounds(self):
        rec = self.layers.get("record")
        if rec is None:
            return
        oor = {}
        for col, (lo, hi) in BOUNDS.items():
            if col not in rec.columns:
                continue
            s    = pd.to_numeric(rec[col], errors="coerce").dropna()
            nbad = int(((s < lo) | (s > hi)).sum())
            if nbad:
                oor[col] = nbad
                self.report.warnings.append(
                    f"'{col}': {nbad} value(s) outside [{lo}, {hi}]."
                )
        self.report.out_of_range["record"] = oor

    def _evaluate(self):
        crit = [w for w in self.report.warnings if "negative timestamp" in w.lower()]
        self.report.overall_pass = len(crit) == 0

    def summary_text(self):
        r = self.report
        lines = ["=" * 56, "DATA QUALITY REPORT", "=" * 56]
        for name, info in r.layer_summaries.items():
            lines.append(
                f"  [{name.upper()}]  {info['rows']} rows | "
                f"dups={info['duplicates']} | miss_cols={info['missing_columns']}"
            )
        oor = r.out_of_range.get("record", {})
        lines.append("\n[SENSOR BOUNDS]")
        if oor:
            for c, n in oor.items():
                lines.append(f"  {c}: {n} violation(s)")
        else:
            lines.append("  None.")
        lines.append("\n[TIMESTAMPS]")
        for t in r.timestamp_issues:
            lines.append(f"  {t}")
        if r.warnings:
            lines.append("\n[WARNINGS]")
            for w in r.warnings:
                lines.append(f"  ! {w}")
        lines.append(f"\nRESULT: {'PASS' if r.overall_pass else 'FAIL'}")
        lines.append("=" * 56)
        return "\n".join(lines)