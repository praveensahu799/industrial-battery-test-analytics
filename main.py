import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")

BASE     = Path(__file__).parent
DATA_RAW = BASE / "data" / "raw"
FIGURES  = BASE / "reports" / "figures"
SUMMARY  = BASE / "reports" / "summary"
DATASET  = DATA_RAW / "INEVYD51105B0012 100% DOD  B-SMART  06.05.2025.xlsx"

FIGURES.mkdir(parents=True, exist_ok=True)
SUMMARY.mkdir(parents=True, exist_ok=True)


def main():
    logger.info("=" * 60)
    logger.info("  INDUSTRIAL BATTERY TEST ANALYTICS")
    logger.info("=" * 60)

    # ── 1. Load ──────────────────────────────────────────────────
    logger.info("[1/10] Loading data …")
    from src.loaders.data_loader import BatteryDataLoader
    loader = BatteryDataLoader(DATASET)
    layers = loader.load_all()
    record_df = layers["record"]
    cycle_df  = layers["cycle"]
    step_df   = layers["step"]
    event_df  = layers["event"]
    metadata  = loader.metadata

    # ── 2. Validate ──────────────────────────────────────────────
    logger.info("[2/10] Validating data …")
    from src.preprocessing.validation import DataValidationEngine
    validator = DataValidationEngine(layers)
    dq_report = validator.run()
    print(validator.summary_text())

    # ── 3. Performance analytics ─────────────────────────────────
    logger.info("[3/10] Performance analytics …")
    from src.analytics.performance import PerformanceAnalytics
    perf_engine = PerformanceAnalytics(cycle_df, record_df)
    perf        = perf_engine.compute()
    print(perf_engine.summary_text(perf))

    # ── 4. Charge-discharge analytics ────────────────────────────
    logger.info("[4/10] Charge-discharge analytics …")
    from src.analytics.charge_discharge import ChargeDischargAnalytics
    cd_engine = ChargeDischargAnalytics(record_df, cycle_df)
    cd        = cd_engine.compute()
    print(cd_engine.summary_text(cd))

    # ── 5. Cell voltage analytics ─────────────────────────────────
    logger.info("[5/10] Cell voltage analytics …")
    from src.analytics.cell_voltage import CellVoltageAnalytics
    cell_engine = CellVoltageAnalytics(record_df)
    cell        = cell_engine.compute()
    print(cell_engine.summary_text(cell))

    # ── 6. Thermal analytics ──────────────────────────────────────
    logger.info("[6/10] Thermal analytics …")
    from src.analytics.thermal import ThermalAnalytics
    thermal_engine = ThermalAnalytics(record_df)
    thermal        = thermal_engine.compute()
    print(thermal_engine.summary_text(thermal))

    # ── 7. BMS telemetry analytics ────────────────────────────────
    logger.info("[7/10] BMS telemetry analytics …")
    from src.analytics.bms_telemetry import BMSTelemetryAnalytics
    bms_engine = BMSTelemetryAnalytics(record_df)
    bms        = bms_engine.compute()
    print(bms_engine.summary_text(bms))

    # ── 8. Protection and safety analytics ───────────────────────
    logger.info("[8/10] Protection and safety analytics …")
    from src.analytics.protection_safety import ProtectionSafetyMonitor
    safety_engine = ProtectionSafetyMonitor(record_df)
    safety        = safety_engine.compute()
    print(safety_engine.summary_text(safety))

    # ── 9. Generate all plots ─────────────────────────────────────
    logger.info("[9/10] Generating plots …")
    from src.visualization.plots import (
        plot_voltage_current_profile,
        plot_power_profile,
        plot_capacity_energy_progression,
        plot_cell_voltages_over_time,
        plot_cell_voltage_spread,
        plot_cell_avg_bar,
        plot_temperature_profiles,
        plot_thermal_spread,
        plot_soc_profile,
        plot_bms_vs_cycler_voltage,
        plot_protection_flags,
        plot_mosfet_status,
    )

    plot_voltage_current_profile(record_df, FIGURES)
    logger.info("  Plot 01 done")

    plot_power_profile(record_df, FIGURES)
    logger.info("  Plot 02 done")

    plot_capacity_energy_progression(record_df, FIGURES)
    logger.info("  Plot 03 done")

    plot_cell_voltages_over_time(cell.cell_df, record_df, FIGURES)
    logger.info("  Plot 04 done")

    plot_cell_voltage_spread(cell.spread_series, record_df, FIGURES)
    logger.info("  Plot 05 done")

    plot_cell_avg_bar(cell.cell_avg_V, FIGURES)
    logger.info("  Plot 06 done")

    plot_temperature_profiles(thermal.temp_df, record_df, FIGURES)
    logger.info("  Plot 07 done")

    plot_thermal_spread(thermal.temp_df, record_df, FIGURES)
    logger.info("  Plot 08 done")

    plot_soc_profile(record_df, FIGURES)
    logger.info("  Plot 09 done")

    plot_bms_vs_cycler_voltage(record_df, FIGURES)
    logger.info("  Plot 10 done")

    plot_protection_flags(safety, FIGURES)
    logger.info("  Plot 11 done")

    plot_mosfet_status(record_df, FIGURES)
    logger.info("  Plot 12 done")

    # ── 10. Generate PDF report ───────────────────────────────────
    logger.info("[10/10] Generating PDF report …")
    from src.reporting.report_generator import EngineeringReportGenerator
    report_path = SUMMARY / "battery_engineering_report.pdf"
    generator = EngineeringReportGenerator(
        output_path=report_path,
        figures_dir=FIGURES,
        metadata=metadata,
        perf=perf,
        cd=cd,
        cell=cell,
        thermal=thermal,
        bms=bms,
        safety=safety,
        dq_report=dq_report,
    )
    generator.build()

    logger.info("=" * 60)
    logger.info("  PIPELINE COMPLETE")
    logger.info("  Figures : %s", FIGURES)
    logger.info("  Report  : %s", report_path)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()