import logging
from dataclasses import dataclass, field
import pandas as pd

logger = logging.getLogger(__name__)

CYCLE_MAIN = 2
STEPS_MAIN = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]

BMS_STATUS_MAP = {0: "Normal", 1: "Cell OVP", 2: "Cell UVP", 10: "Pack UVP"}

ALL_FLAGS = {
    "flag_ovp_l1":       "Cell OVP L1",
    "flag_ovp_l2":       "Cell OVP L2",
    "flag_uvp_l1":       "Cell UVP L1",
    "flag_uvp_l2":       "Cell UVP L2",
    "flag_pack_ovp_l1":  "Pack OVP L1",
    "flag_pack_uvp_l1":  "Pack UVP L1",
    "flag_chg_otp_l1":   "Chg OTP L1",
    "flag_dchg_otp_l1":  "Dchg OTP L1",
    "flag_chg_ocp_l1":   "Chg OCP L1",
    "flag_dchg_ocp_l1":  "Dchg OCP L1",
    "flag_soc_high_l1":  "SOC High L1",
    "flag_soc_low_l2":   "SOC Low L2",
    "flag_diff_volt_l1": "Diff Volt L1",
}

LFP_OVP_V = 3.65
LFP_UVP_V = 2.50
LFP_OTP_C = 45.0


@dataclass
class SafetySummary:
    bms_status_counts:   dict
    bms_status_pct:      dict
    flag_counts:         dict
    flag_pct:            dict
    triggered_flags:     list
    chg_mos_on:          int
    chg_mos_off:         int
    dchg_mos_on:         int
    dchg_mos_off:        int
    status_dist:         dict
    actual_max_cell_V:   float
    actual_min_cell_V:   float
    actual_max_temp_C:   float
    actual_peak_dchg_A:  float
    actual_peak_chg_A:   float
    est_ovp_headroom_mV: float
    est_uvp_headroom_mV: float
    est_otp_headroom_C:  float
    safety_pass:         bool
    safety_notes:        list
    c2_df:               pd.DataFrame = field(default_factory=pd.DataFrame)


class ProtectionSafetyMonitor:
    def __init__(self, record_df):
        self._all = record_df
        self._c2  = record_df[record_df["cycle_id"] == CYCLE_MAIN].copy()
        self._c2m = self._c2[self._c2["step_id"].isin(STEPS_MAIN)].copy()

    def compute(self):
        logger.info("Computing protection and safety analytics …")
        rec = self._all
        c2  = self._c2
        c2m = self._c2m

        def n(col, df):
            if col not in df.columns:
                return pd.Series(dtype=float, index=df.index)
            return pd.to_numeric(df[col], errors="coerce")

        bms_stat  = n("bms_status", rec).dropna().astype(int)
        total_all = max(len(rec), 1)
        bms_counts = {}
        bms_pct    = {}
        for code, label in BMS_STATUS_MAP.items():
            cnt = int((bms_stat == code).sum())
            bms_counts[label] = cnt
            bms_pct[label]    = round(cnt / total_all * 100, 2)

        n_c2 = max(len(c2), 1)
        flag_counts = {}
        flag_pct    = {}
        triggered   = []
        for col, label in ALL_FLAGS.items():
            s   = n(col, c2).fillna(0)
            cnt = int((s == 1).sum())
            flag_counts[label] = cnt
            flag_pct[label]    = round(cnt / n_c2 * 100, 2)
            if cnt > 0:
                triggered.append(label)

        chg_mos  = n("chg_mos_status",  c2).fillna(0)
        dchg_mos = n("dchg_mos_status", c2).fillna(0)
        cds      = n("chg_dchg_status", c2).dropna().astype(int)
        cds_map  = {0: "Idle", 1: "Charging", 2: "Discharging"}
        status_dist = {cds_map.get(k, str(k)): int(v)
                       for k, v in cds.value_counts().items()}

        max_cv  = float(n("max_cell_volt_V", c2m).max()) if "max_cell_volt_V" in c2m.columns else 0.0
        min_cv  = float(n("min_cell_volt_V", c2m).min()) if "min_cell_volt_V" in c2m.columns else 0.0
        max_T   = float(n("max_cell_temp_C", c2m).max()) if "max_cell_temp_C" in c2m.columns else 0.0
        pk_dchg = float(n("current_A", c2m).abs().max())
        pk_chg  = float(n("current_A", c2m).max())

        est_ovp = (LFP_OVP_V - max_cv) * 1000.0 if max_cv > 0 else 0.0
        est_uvp = (min_cv - LFP_UVP_V) * 1000.0 if min_cv > 0 else 0.0
        est_otp = LFP_OTP_C - max_T              if max_T  > 0 else 0.0

        notes       = []
        safety_pass = True
        ovp_ev = bms_counts.get("Cell OVP", 0)
        if ovp_ev > 0:
            notes.append(f"BMS OVP events: {ovp_ev} records.")
            safety_pass = False
        if not notes:
            notes.append("No critical protection events detected.")

        return SafetySummary(
            bms_status_counts=bms_counts,
            bms_status_pct=bms_pct,
            flag_counts=flag_counts,
            flag_pct=flag_pct,
            triggered_flags=triggered,
            chg_mos_on=int((chg_mos == 1).sum()),
            chg_mos_off=int((chg_mos == 0).sum()),
            dchg_mos_on=int((dchg_mos == 1).sum()),
            dchg_mos_off=int((dchg_mos == 0).sum()),
            status_dist=status_dist,
            actual_max_cell_V=max_cv,
            actual_min_cell_V=min_cv,
            actual_max_temp_C=max_T,
            actual_peak_dchg_A=pk_dchg,
            actual_peak_chg_A=pk_chg,
            est_ovp_headroom_mV=est_ovp,
            est_uvp_headroom_mV=est_uvp,
            est_otp_headroom_C=est_otp,
            safety_pass=safety_pass,
            safety_notes=notes,
            c2_df=c2,
        )

    def summary_text(self, s):
        lines = [
            "=" * 56, "PROTECTION & SAFETY", "=" * 56,
            "  [BMS STATUS]",
        ]
        for label, cnt in s.bms_status_counts.items():
            lines.append(f"    {label}: {cnt} ({s.bms_status_pct[label]:.1f}%)")
        lines.append("  [TRIGGERED FLAGS]")
        for lbl in (s.triggered_flags if s.triggered_flags else ["None"]):
            cnt = s.flag_counts.get(lbl, 0)
            lines.append(f"    {lbl}: {cnt}")
        lines += [
            f"  Max cell V   : {s.actual_max_cell_V:.3f} V",
            f"  Min cell V   : {s.actual_min_cell_V:.3f} V",
            f"  Max temp     : {s.actual_max_temp_C:.1f} °C",
            f"  Est OVP hdm  : {s.est_ovp_headroom_mV:.0f} mV",
            f"  Est UVP hdm  : {s.est_uvp_headroom_mV:.0f} mV",
            f"  Est OTP hdm  : {s.est_otp_headroom_C:.1f} °C",
            f"  SAFETY       : {'PASS' if s.safety_pass else 'FAIL'}",
            "=" * 56,
        ]
        return "\n".join(lines)