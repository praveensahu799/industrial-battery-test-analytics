import logging
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

logger = logging.getLogger(__name__)

PAGE_W, PAGE_H = A4
MARGIN = 2.0 * cm

CB   = colors.HexColor("#1A237E")
CACC = colors.HexColor("#1565C0")
CLB  = colors.HexColor("#E3F2FD")
CLG  = colors.HexColor("#ECEFF1")
CGR  = colors.HexColor("#546E7A")
CRED = colors.HexColor("#B71C1C")
CGRN = colors.HexColor("#1B5E20")
CAMB = colors.HexColor("#E65100")


def _sty(name, **kw):
    return ParagraphStyle(name, **kw)


STYLES = {
    "title": _sty("title", fontName="Helvetica-Bold", fontSize=22,
                  textColor=CB, spaceAfter=6, alignment=1),
    "sub":   _sty("sub",   fontName="Helvetica",      fontSize=12,
                  textColor=CGR, spaceAfter=4, alignment=1),
    "sec":   _sty("sec",   fontName="Helvetica-Bold", fontSize=13,
                  textColor=CACC, spaceBefore=14, spaceAfter=4),
    "ssec":  _sty("ssec",  fontName="Helvetica-Bold", fontSize=11,
                  textColor=CGR, spaceBefore=8, spaceAfter=3),
    "body":  _sty("body",  fontName="Helvetica",      fontSize=9.5,
                  textColor=colors.black, spaceAfter=4, leading=13, alignment=4),
    "kk":    _sty("kk",    fontName="Helvetica-Bold", fontSize=9,  textColor=CGR),
    "kv":    _sty("kv",    fontName="Helvetica",      fontSize=9,  textColor=colors.black),
    "cap":   _sty("cap",   fontName="Helvetica-Oblique", fontSize=8.5,
                  textColor=CGR, alignment=1, spaceAfter=4),
    "good":  _sty("good",  fontName="Helvetica", fontSize=9.5,
                  textColor=CGRN, spaceAfter=3, leftIndent=12),
    "warn":  _sty("warn",  fontName="Helvetica", fontSize=9.5,
                  textColor=CAMB, spaceAfter=3, leftIndent=12),
    "fail":  _sty("fail",  fontName="Helvetica", fontSize=9.5,
                  textColor=CRED, spaceAfter=3, leftIndent=12),
    "bul":   _sty("bul",   fontName="Helvetica", fontSize=9.5,
                  textColor=colors.black, spaceAfter=2, leftIndent=12, leading=13),
}


def P(text, style="body"):
    return Paragraph(text, STYLES[style])


def SP(h=0.3):
    return Spacer(1, h * cm)


def HR():
    return HRFlowable(width="100%", thickness=1.5, color=CACC, spaceAfter=2)


def IMG(path, width=15 * cm):
    p = Path(path)
    if not p.exists():
        return None
    img = Image(str(p))
    ar = img.imageHeight / img.imageWidth
    img.drawWidth  = width
    img.drawHeight = width * ar
    return img


def KV_TABLE(rows, w1=6 * cm, w2=9 * cm):
    data = [[P(str(k), "kk"), P(str(v), "kv")] for k, v in rows]
    t = Table(data, colWidths=[w1, w2])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, CLG]),
        ("GRID",          (0, 0), (-1, -1), 0.3, CGR),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def HDR_FOOTER(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(CB)
    canvas.rect(0, h - 1.0 * cm, w, 1.0 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(MARGIN, h - 0.65 * cm,
                      "INDUSTRIAL BATTERY TEST ANALYTICS — CONFIDENTIAL")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - MARGIN, h - 0.65 * cm, f"Page {doc.page}")
    canvas.setFillColor(CLG)
    canvas.rect(0, 0, w, 0.8 * cm, fill=1, stroke=0)
    canvas.setFillColor(CGR)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(MARGIN, 0.28 * cm,
                      f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  "
                      f"Battery Test Analytics System")
    canvas.drawRightString(w - MARGIN, 0.28 * cm,
                           "Test ID: INEVYD51105B0012  |  100% DOD B-SMART")
    canvas.restoreState()


class EngineeringReportGenerator:
    def __init__(self, output_path, figures_dir, metadata,
                 perf, cd, cell, thermal, bms, safety, dq_report):
        self.output_path = Path(output_path)
        self.fig_dir     = Path(figures_dir)
        self.meta        = metadata
        self.perf        = perf
        self.cd          = cd
        self.cell        = cell
        self.thermal     = thermal
        self.bms         = bms
        self.safety      = safety
        self.dq          = dq_report
        self.story       = []

    def _add(self, *items):
        for it in items:
            if it is not None:
                self.story.append(it)

    def _fig(self, fname, caption="", width=15 * cm):
        img = IMG(self.fig_dir / fname, width)
        if img:
            self._add(SP(0.2), img)
            if caption:
                self._add(P(caption, "cap"))
            self._add(SP(0.2))

    def _cover(self):
        m = self.meta
        self._add(
            SP(3),
            P("INDUSTRIAL BATTERY TEST ANALYTICS", "title"),
            P("Engineering Report", "sub"),
            P("BMS Monitoring & Performance Analysis", "sub"),
            SP(1.5),
        )
        rows = [
            ("Test ID",       m.get("test_id", "")),
            ("Test Profile",  m.get("test_profile", "")),
            ("Dataset",       m.get("filename", "")),
            ("Test Start",    str(m.get("test_start", ""))[:19]),
            ("Test End",      str(m.get("test_end",   ""))[:19]),
            ("Duration",      f"{m.get('test_duration_h', 0):.2f} h"),
            ("Total Records", f"{m.get('total_records', 0):,}"),
            ("Cycles",        str(m.get("total_cycles", ""))),
            ("Cell Count",    str(m.get("num_cells", 16))),
            ("Report Date",   datetime.now().strftime("%Y-%m-%d %H:%M")),
        ]
        self._add(KV_TABLE(rows))
        self._add(PageBreak())

    def _data_quality(self):
        dq = self.dq
        self._add(HR(), P("1. Data Quality Summary", "sec"))
        ok = dq.overall_pass
        color_str = "green" if ok else "red"
        verdict   = "PASS &#10003;" if ok else "FAIL &#10007;"
        self._add(P(f"Overall: <b><font color='{color_str}'>{verdict}</font></b>"))
        data = [["Layer", "Rows", "Cols", "Dups", "Miss Cols"]]
        for name, info in dq.layer_summaries.items():
            data.append([
                name.upper(), str(info["rows"]), str(info["columns"]),
                str(info["duplicates"]), str(info["missing_columns"]),
            ])
        t = Table(data, colWidths=[3 * cm, 2.5 * cm, 2 * cm, 2.5 * cm, 3 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), CB),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("GRID",          (0, 0), (-1, -1), 0.4, CGR),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, CLG]),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        self._add(t)
        if dq.warnings:
            self._add(SP(0.3), P("Warnings:", "ssec"))
            for w in dq.warnings:
                self._add(P(f"• {w}", "bul"))

    def _performance(self):
        ps = self.perf
        self._add(HR(), P("2. Battery Performance Summary", "sec"))
        rows = [
            ("Charge Capacity",        f"{ps.chg_capacity_Ah:.3f} Ah"),
            ("Discharge Capacity",     f"{ps.dchg_capacity_Ah:.3f} Ah"),
            ("Charge Energy",          f"{ps.chg_energy_Wh:.1f} Wh"),
            ("Discharge Energy",       f"{ps.dchg_energy_Wh:.1f} Wh"),
            ("Coulombic Efficiency",   f"{ps.coulombic_efficiency_pct:.3f} %"),
            ("Energy Efficiency",      f"{ps.energy_efficiency_pct:.3f} %"),
            ("Charge Mid-Voltage",     f"{ps.chg_mid_volt_V:.3f} V"),
            ("Discharge Mid-Voltage",  f"{ps.dchg_mid_volt_V:.3f} V"),
            ("Charge Duration",        f"{ps.chg_time_h:.2f} h"),
            ("Discharge Duration",     f"{ps.dchg_time_h:.2f} h"),
            ("Peak Charge Current",    f"{ps.peak_chg_current_A:.1f} A  ({ps.chg_c_rate:.2f}C)"),
            ("Peak Discharge Current", f"{ps.peak_dchg_current_A:.1f} A  ({ps.dchg_c_rate:.2f}C)"),
            ("Avg Charge Power",       f"{ps.avg_chg_power_W:.1f} W"),
            ("Avg Discharge Power",    f"{ps.avg_dchg_power_W:.1f} W"),
            ("Peak Pack Voltage",      f"{ps.peak_pack_voltage_V:.3f} V"),
            ("Min Pack Voltage",       f"{ps.min_pack_voltage_V:.3f} V"),
        ]
        self._add(KV_TABLE(rows))
        self._add(SP(0.3), P(
            "Coulombic Efficiency above 99.5% indicates minimal parasitic side reactions. "
            "Energy Efficiency reflects total round-trip losses including ohmic heating. "
            "C-rate is referenced to the measured discharge capacity.", "body"
        ))

    def _charge_discharge(self):
        cd = self.cd
        self._add(HR(), P("3. Charge–Discharge Profile Analysis", "sec"))
        self._add(P("3.1  Voltage & Current Profile", "ssec"))
        self._fig("01_voltage_current_profile.png",
                  "Figure 1 — Pack voltage and current vs elapsed time.")
        self._add(P("3.2  Power Profile", "ssec"))
        self._fig("02_power_profile.png",
                  "Figure 2 — Pack power profile. Positive = charge; Negative = discharge.")
        self._add(P("3.3  Cumulative Capacity & Energy", "ssec"))
        self._fig("03_capacity_energy.png",
                  "Figure 3 — Cumulative capacity (0 to ~110 Ah) and energy (0 to ~5967 Wh).")
        self._add(P("3.4  Summary Metrics", "ssec"))
        rows = [
            ("Charge start voltage",    f"{cd.chg_start_volt_V:.3f} V"),
            ("Charge end voltage",      f"{cd.chg_end_volt_V:.3f} V"),
            ("Charge peak power",       f"{cd.chg_peak_power_W:.1f} W"),
            ("CC phase duration",       f"{cd.chg_cc_duration_h:.2f} h"),
            ("CV phase duration",       f"{cd.chg_cv_duration_h:.2f} h"),
            ("Charge mid-voltage",      f"{cd.chg_mid_volt_V:.3f} V"),
            ("Discharge start voltage", f"{cd.dchg_start_volt_V:.3f} V"),
            ("Discharge end voltage",   f"{cd.dchg_end_volt_V:.3f} V"),
            ("Discharge peak power",    f"{cd.dchg_peak_power_W:.1f} W"),
            ("Discharge avg power",     f"{cd.dchg_avg_power_W:.1f} W"),
            ("Discharge mid-voltage",   f"{cd.dchg_mid_volt_V:.3f} V"),
            ("Rest post-charge V",      f"{cd.rest_post_chg_volt_V:.3f} V"),
            ("Rest post-discharge V",   f"{cd.rest_post_dchg_volt_V:.3f} V"),
            ("Voltage hysteresis",      f"{cd.voltage_hysteresis_V:.3f} V"),
        ]
        self._add(KV_TABLE(rows))

    def _cell_voltage(self):
        cv = self.cell
        self._add(HR(), P("4. Cell Voltage Analysis", "sec"))
        self._add(P("4.1  Individual Cell Voltages", "ssec"))
        self._fig("04_cell_voltages_time.png",
                  "Figure 4 — All 16 cell voltages over the full test duration.")
        self._add(P("4.2  Voltage Spread", "ssec"))
        self._fig("05_cell_voltage_spread.png",
                  "Figure 5 — Cell voltage spread with 50 mV imbalance threshold.")
        self._add(P("4.3  Per-Cell Average Voltage", "ssec"))
        self._fig("06_cell_avg_bar.png",
                  "Figure 6 — Per-cell average voltage. Red dashed line = pack average.")
        self._add(P("4.4  Imbalance Summary", "ssec"))
        rows = [
            ("Average spread",         f"{cv.avg_spread_V * 1000:.1f} mV"),
            ("Peak spread",            f"{cv.max_spread_V * 1000:.1f} mV"),
            ("Minimum spread",         f"{cv.min_spread_V * 1000:.1f} mV"),
            ("Weakest cell",           f"{cv.weakest_cell}  (avg {cv.weakest_avg_V:.4f} V)"),
            ("Strongest cell",         f"{cv.strongest_cell}  (avg {cv.strongest_avg_V:.4f} V)"),
            ("Cell-to-cell avg delta", f"{(cv.strongest_avg_V - cv.weakest_avg_V) * 1000:.1f} mV"),
            ("Imbalance flag (>50mV)", "YES" if cv.imbalance_flag else "NO"),
        ]
        self._add(KV_TABLE(rows))

    def _thermal(self):
        th = self.thermal
        self._add(HR(), P("5. Thermal Analysis", "sec"))
        self._fig("07_temperature_profiles.png",
                  "Figure 7 — Thermistor temperature profiles over test. 45 C threshold shown.")
        self._fig("08_thermal_spread.png",
                  "Figure 8 — Sensor-to-sensor thermal spread. 5 C threshold shown.")
        rows = [
            ("Peak temperature",         f"{th.global_max_C:.1f} C"),
            ("Minimum temperature",      f"{th.global_min_C:.1f} C"),
            ("Average temperature",      f"{th.global_avg_C:.1f} C"),
            ("Std deviation",            f"{th.global_std_C:.2f} C"),
            ("Avg sensor spread",        f"{th.avg_spread_C:.2f} C"),
            ("Max sensor spread",        f"{th.max_spread_C:.2f} C"),
            ("Avg temp during charge",   f"{th.chg_avg_temp_C:.1f} C"),
            ("Avg temp during discharge",f"{th.dchg_avg_temp_C:.1f} C"),
            ("Avg temp during rest",     f"{th.rest_avg_temp_C:.1f} C"),
            ("BMS max temp (avg)",       f"{th.bms_max_temp_avg_C:.1f} C"),
            ("Hotspot flag (>=45 C)",    "YES" if th.hotspot_flag else "NO"),
            ("Spread flag (>5 C)",       "YES" if th.spread_flag  else "NO"),
        ]
        self._add(KV_TABLE(rows))

    def _bms(self):
        b = self.bms
        self._add(HR(), P("6. BMS Telemetry Analysis", "sec"))
        self._fig("09_soc_profile.png",
                  "Figure 9 — BMS SOC: rises 0 to 100% during charge; falls 100 to 0% during discharge.")
        self._fig("10_bms_vs_cycler_voltage.png",
                  "Figure 10 — BMS vs cycler voltage overlay and discrepancy trace (mV).")
        rows = [
            ("SOC start",            f"{b.soc_start_pct:.1f} %"),
            ("SOC end",              f"{b.soc_end_pct:.1f} %"),
            ("SOC range",            f"{b.soc_min_pct:.1f} – {b.soc_max_pct:.1f} %"),
            ("Residual cap (peak)",  f"{b.residual_cap_max_Ah:.3f} Ah"),
            ("Residual cap (start)", f"{b.residual_cap_start_Ah:.3f} Ah"),
            ("Residual cap (end)",   f"{b.residual_cap_end_Ah:.3f} Ah"),
            ("BMS avg voltage",      f"{b.bms_volt_avg_V:.3f} V"),
            ("Cycler avg voltage",   f"{b.cycler_volt_avg_V:.3f} V"),
            ("Voltage discrepancy",  f"{b.volt_discrepancy_avg_mV:+.1f} mV"),
            ("BMS cycle count",      f"{b.bms_cycle_count_start} to {b.bms_cycle_count_end}"),
        ]
        self._add(KV_TABLE(rows))
        self._add(SP(0.3), P(
            "Residual_Capacity(AH) is the BMS remaining-capacity register (0 to 110 Ah). "
            "Voltage discrepancy reflects sensing-point differences between BMS terminals "
            "and cycler cable measurement points. Values within +/-200 mV are acceptable.", "body"
        ))

    def _safety(self):
        sf = self.safety
        self._add(HR(), P("7. Protection & Safety Analysis", "sec"))
        self._add(P(
            "Protection columns in this B-SMART export are binary status flags "
            "(0 = not triggered, 1 = triggered). No threshold values are exported "
            "by this cycler software. Operating margins are estimated against "
            "typical LFP BMS reference values.", "body"
        ))
        self._fig("11_protection_flags.png",
                  "Figure 11 — Protection flag activation timeline and BMS_Status over Cycle 2.")
        self._fig("12_mosfet_status.png",
                  "Figure 12 — Charge and discharge MOSFET states over Cycle 2.")
        rows = [
            ("Peak cell voltage",      f"{sf.actual_max_cell_V:.3f} V"),
            ("Min cell voltage",       f"{sf.actual_min_cell_V:.3f} V"),
            ("Peak temperature",       f"{sf.actual_max_temp_C:.1f} C"),
            ("Peak charge current",    f"{sf.actual_peak_chg_A:.1f} A"),
            ("Peak discharge current", f"{sf.actual_peak_dchg_A:.1f} A"),
            ("Est. OVP headroom",      f"{sf.est_ovp_headroom_mV:.0f} mV  (ref 3.65 V/cell)"),
            ("Est. UVP headroom",      f"{sf.est_uvp_headroom_mV:.0f} mV  (ref 2.50 V/cell)"),
            ("Est. OTP headroom",      f"{sf.est_otp_headroom_C:.1f} C   (ref 45 C)"),
            ("Triggered flags",        ", ".join(sf.triggered_flags) if sf.triggered_flags else "None"),
            ("Safety verdict",         "PASS" if sf.safety_pass else "FAIL"),
        ]
        self._add(KV_TABLE(rows))
        self._add(SP(0.3))
        for note in sf.safety_notes:
            style = "good" if "No critical" in note else "warn"
            self._add(P(f"• {note}", style))

    def _findings(self):
        ps = self.perf
        cv = self.cell
        th = self.thermal
        sf = self.safety
        self._add(HR(), P("8. Key Findings", "sec"))

        self._add(P("Performance", "ssec"))
        ce_ok = ps.coulombic_efficiency_pct >= 99.0
        ee_ok = ps.energy_efficiency_pct    >= 90.0
        self._add(
            P(f"• Coulombic Efficiency {ps.coulombic_efficiency_pct:.3f}% — "
              f"{'Excellent (>=99%)' if ce_ok else 'Below target (<99%)'}",
              "good" if ce_ok else "warn"),
            P(f"• Energy Efficiency {ps.energy_efficiency_pct:.3f}% — "
              f"{'Good (>=90%)' if ee_ok else 'Below target (<90%)'}",
              "good" if ee_ok else "warn"),
            P(f"• Battery delivered {ps.dchg_capacity_Ah:.3f} Ah at "
              f"{ps.dchg_c_rate:.2f}C with discharge mid-point voltage "
              f"{ps.dchg_mid_volt_V:.3f} V.", "body"),
        )
        self._add(P("Cell Uniformity", "ssec"))
        self._add(
            P(f"• Average spread {cv.avg_spread_V * 1000:.1f} mV — "
              f"{'Imbalance detected (>50 mV)' if cv.imbalance_flag else 'Within limits (<50 mV)'}",
              "warn" if cv.imbalance_flag else "good"),
            P(f"• Weakest cell: {cv.weakest_cell} at {cv.weakest_avg_V:.4f} V avg. "
              f"Strongest: {cv.strongest_cell} at {cv.strongest_avg_V:.4f} V avg.", "body"),
        )
        self._add(P("Thermal Behaviour", "ssec"))
        self._add(
            P(f"• Peak temperature {th.global_max_C:.1f} C — "
              f"{'Hotspot condition' if th.hotspot_flag else 'Within normal range (<45 C)'}",
              "warn" if th.hotspot_flag else "good"),
            P(f"• Max sensor spread {th.max_spread_C:.2f} C — "
              f"{'Non-uniform thermal distribution' if th.spread_flag else 'Uniform (<5 C spread)'}",
              "warn" if th.spread_flag else "good"),
        )
        self._add(P("Safety", "ssec"))
        self._add(
            P(f"• Overall safety verdict: {'PASS' if sf.safety_pass else 'FAIL'}",
              "good" if sf.safety_pass else "fail"),
        )

    def _recommendations(self):
        self._add(HR(), P("9. Recommendations & Limitations", "sec"))
        self._add(P("Recommendations", "ssec"))
        recs = [
            "Monitor the weakest cell over subsequent cycles to detect early capacity divergence.",
            "Verify BMS passive balancing activation during the CV phase if cell spread increases.",
            "Schedule a DCIR measurement after completing additional cycles to establish a resistance baseline.",
            "Cross-validate BMS voltage calibration against the cycler periodically.",
            "Validate thermal management adequacy for ambient conditions above 30 C.",
        ]
        for r in recs:
            self._add(P(f"• {r}", "bul"))
        self._add(SP(0.3), P("Limitations", "ssec"))
        lims = [
            "Single test cycle (100% DOD B-SMART). Cycle-life trends require multi-cycle data.",
            "BMS telemetry sample rate is lower than cycler record rate; fast transients may not be captured.",
            "No Reference Performance Test (RPT) data available; all values are interpreted in isolation.",
            "Temperature coverage is limited to four thermistors; full spatial distribution is not characterised.",
            "Protection threshold values are not exported by this cycler; margins are engineering estimates only.",
            "SOH, RUL, and degradation modelling are outside the scope of this report.",
        ]
        for lim in lims:
            self._add(P(f"• {lim}", "bul"))

    def build(self):
        logger.info("Building PDF report: %s", self.output_path)
        doc = BaseDocTemplate(
            str(self.output_path),
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )
        frame = Frame(
            MARGIN, 1.5 * cm,
            PAGE_W - 2 * MARGIN, PAGE_H - 3.5 * cm,
            id="main",
        )
        tmpl = PageTemplate(id="main", frames=[frame], onPage=HDR_FOOTER)
        doc.addPageTemplates([tmpl])

        self._cover()
        self._data_quality()
        self.story.append(PageBreak())
        self._performance()
        self.story.append(PageBreak())
        self._charge_discharge()
        self.story.append(PageBreak())
        self._cell_voltage()
        self.story.append(PageBreak())
        self._thermal()
        self.story.append(PageBreak())
        self._bms()
        self.story.append(PageBreak())
        self._safety()
        self.story.append(PageBreak())
        self._findings()
        self._recommendations()

        doc.build(self.story)
        logger.info("PDF saved: %s", self.output_path)
        return self.output_path