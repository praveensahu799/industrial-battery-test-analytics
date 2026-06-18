import logging
import re
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

CYCLE_MAIN = 2
STEPS_ALL  = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
STEPS_CHG  = [5.0, 6.0, 7.0]
STEPS_DCHG = [9.0, 10.0]
STEPS_REST = [8.0, 11.0]

RECORD_RENAME = {
    "Cycle ID": "cycle_id", "Step ID": "step_id", "Record ID": "record_id",
    "Step State": "step_state", "Test Event": "test_event",
    "System Time": "system_time", "Relative Time(Sec)": "rel_time_s",
    "Voltage(V)": "voltage_V", "Current(A)": "current_A",
    "Capacity(Ah)": "step_cap_Ah", "Energy(Wh)": "step_eng_Wh",
    "DCIR(mO)": "dcir_mOhm", "POWER(W)": "power_W", "Mode": "mode",
    "Battery_Temperature(?)": "battery_temp_C",
    "SOC": "soc_pct",
    "Demand_Voltage(V)": "demand_volt_V", "Demand_Current(A)": "demand_curr_A",
    "BMS_Voltage(V)": "bms_voltage_V", "BMS_Current(A)": "bms_current_A",
    "Fixed1": "fixed1", "Fixed2": "fixed2",
    "Cell_Thermistor1": "thermistor1_C", "Cell_Thermistor2": "thermistor2_C",
    "Cell_Thermistor3": "thermistor3_C", "Cell_Thermistor4": "thermistor4_C",
    "Cycles": "bms_cycle_count", "Load_Status.": "load_status",
    "Battery_Capacity(mAH)": "bms_cap_raw",
    "Ambient_Sensor": "ambient_temp_C", "MOSFET_Temperature": "mosfet_temp_C",
    "BMS_Status": "bms_status", "CANIDABCDEF_Mux": "can_mux",
    "MAX_CELL_VOLTAGE(V)": "max_cell_volt_V",
    "No_Of_Max_Cell_Voltage": "max_cell_no",
    "MIN_CELL_VOLTAGE(V)": "min_cell_volt_V",
    "No_Of_Min_Cell_Voltage": "min_cell_no",
    "MAX_CELL_TEMPERATURE(°C)": "max_cell_temp_C",
    "Max_Temp_CellNo": "max_temp_cell_no",
    "MIN_CELL_TEMPERATURE(°C)": "min_cell_temp_C",
    "Min_Temp_CellNo": "min_temp_cell_no",
    "Charge_Discharge_Status": "chg_dchg_status",
    "Charge_MOS_Tube_Status": "chg_mos_status",
    "Discharge_MOS_Tube_Status": "dchg_mos_status",
    "BMS_Life": "bms_life",
    "Residual_Capacity(AH)": "residual_cap_Ah",
    "NUMBER_OF_CELLS": "num_cells",
    "NUMBER_OF_TEMPERATURE_SENSORS": "num_temp_sensors",
    "Frame_Number": "frame_number",
    "Cell_Voltage1(V)": "cell1_V", "Cell_Voltage2(V)": "cell2_V",
    "Cell_Voltage3(V)": "cell3_V", "Cell_Voltage4(V)": "cell4_V",
    "Cell_Voltage5(V)": "cell5_V", "Cell_Voltage6(V)": "cell6_V",
    "Cell_Voltage7(V)": "cell7_V", "Cell_Voltage8(V)": "cell8_V",
    "Cell_Voltage9(V)": "cell9_V", "Cell_Voltage10(V)": "cell10_V",
    "Cell_Voltage11(V)": "cell11_V", "Cell_Voltage12(V)": "cell12_V",
    "Cell_Voltage13(V)": "cell13_V", "Cell_Voltage14(V)": "cell14_V",
    "Cell_Voltage15(V)": "cell15_V", "Cell_Voltage16(V)": "cell16_V",
    "Cell_Volt_High_Level_1": "flag_ovp_l1",
    "Cell_Volt_High_Level_2": "flag_ovp_l2",
    "Cell_Volt_Low_Level_1":  "flag_uvp_l1",
    "Cell_Volt_Low_Level_2":  "flag_uvp_l2",
    "Sum_Volt_High_Level_1":  "flag_pack_ovp_l1",
    "Sum_Volt_High_Level_2":  "flag_pack_ovp_l2",
    "Sum_Volt_Low_Level_1":   "flag_pack_uvp_l1",
    "Sum_Volt_Low_Level_2":   "flag_pack_uvp_l2",
    "Chg_Temp_High_Level_1":  "flag_chg_otp_l1",
    "Chg_Temp_High_Level_2":  "flag_chg_otp_l2",
    "Chg_Temp_Low_Level_1":   "flag_chg_utp_l1",
    "Chg_Temp_Low_Level_2":   "flag_chg_utp_l2",
    "Dischg_Temp_High_Level_1": "flag_dchg_otp_l1",
    "Dischg_Temp_High_Level_2": "flag_dchg_otp_l2",
    "Dischg_Temp_Low_Level_1":  "flag_dchg_utp_l1",
    "Dischg_Temp_Low_Level_2":  "flag_dchg_utp_l2",
    "Chg_Overcurrent_Level_1":  "flag_chg_ocp_l1",
    "Chg_Overcurrent_Level_2":  "flag_chg_ocp_l2",
    "Dischg_Overcurrent_Level_1": "flag_dchg_ocp_l1",
    "Dischg_Overcurrent_Level_2": "flag_dchg_ocp_l2",
    "SO C_High_Level_1": "flag_soc_high_l1",
    "SO C_High_Level_2": "flag_soc_high_l2",
    "SO C_Low_Level_1":  "flag_soc_low_l1",
    "SO C_Low_Level_2":  "flag_soc_low_l2",
    "Diff_Volt_Level_1": "flag_diff_volt_l1",
    "Diff_Volt_Level_2": "flag_diff_volt_l2",
    "Diff_Temp_Level_1": "flag_diff_temp_l1",
    "Diff_Temp_Level_2": "flag_diff_temp_l2",
    "Fixed3": "fixed3", "Fixed4": "fixed4",
}

CYCLE_RENAME = {
    "Cycle": "cycle",
    "Charge Mid. Volt(V)": "chg_mid_volt_V",
    "Discharge Mid Volt(V)": "dchg_mid_volt_V",
    "Capacity(Ah)": "capacity_Ah",
    "Charge Capacity(Ah)": "chg_capacity_Ah",
    "Discharge Capacity(Ah)": "dchg_capacity_Ah",
    "Efficiency(%)": "coulombic_efficiency_pct",
    "Capacity retention rate(%)": "capacity_retention_pct",
    "Energy(Wh)": "energy_Wh",
    "Charge Energy(Wh)": "chg_energy_Wh",
    "Discharge Energy(Wh)": "dchg_energy_Wh",
    "Energy Efficiency(%)": "energy_efficiency_pct",
    "Charge Time(Sec)": "chg_time_s",
    "Discharge Time(Sec)": "dchg_time_s",
    "Vol diff(V)": "volt_diff_V",
    "Discharge end time": "dchg_end_time",
    "Accumulated charging capacity(Ah)": "accum_chg_cap_Ah",
    "Accumulated discharge capacity(Ah)": "accum_dchg_cap_Ah",
    "Accumulated charging energy(Wh)": "accum_chg_energy_Wh",
    "Accumulated discharge energy(Wh)": "accum_dchg_energy_Wh",
}

STEP_RENAME = {
    "Step": "step_label", "Process": "process", "Mode": "mode",
    "Set Volt(V)": "set_volt_V", "Set Current(A)": "set_current_A",
    "Status": "status", "Capacity(Ah)": "capacity_Ah",
    "Charge Capacity(Ah)": "chg_capacity_Ah",
    "Discharge Capacity(Ah)": "dchg_capacity_Ah",
    "Energy(Wh)": "energy_Wh", "Charge Energy(Wh)": "chg_energy_Wh",
    "Discharge Energy(Wh)": "dchg_energy_Wh",
    "Step Time(Sec)": "step_time_s", "Start Volt(V)": "start_volt_V",
    "End Volt(V)": "end_volt_V", "DCIR1(mO)": "dcir1_mOhm",
    "DCIR2(mO)": "dcir2_mOhm", "End Condition": "end_condition",
    "Goto Dec": "goto_dec",
}

EVENT_RENAME = {
    "No": "event_no", "Record ID": "record_id",
    "event description": "description", "Time": "time",
}


def _is_bsmart_header(val):
    if pd.isna(val):
        return False
    return bool(re.search(r":\s*\d+\s+\w+.*\(.*\).*Ah", str(val)))


class BatteryDataLoader:
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise FileNotFoundError(str(self.filepath))
        self._xl = None
        self.cycle_df  = None
        self.step_df   = None
        self.record_df = None
        self.event_df  = None
        self.metadata  = {}

    def load_all(self):
        logger.info("Loading %s", self.filepath.name)
        self._xl = pd.ExcelFile(self.filepath)
        self.cycle_df  = self._load_cycle()
        self.step_df   = self._load_step()
        self.record_df = self._load_record()
        self.event_df  = self._load_event()
        self._build_metadata()
        logger.info(
            "Loaded | cycle=%d step=%d record=%d event=%d",
            len(self.cycle_df), len(self.step_df),
            len(self.record_df), len(self.event_df),
        )
        return {
            "cycle":  self.cycle_df,
            "step":   self.step_df,
            "record": self.record_df,
            "event":  self.event_df,
        }

    def _load_cycle(self):
        df = pd.read_excel(self._xl, sheet_name="Cycle Layer")
        df = df.rename(columns=CYCLE_RENAME)
        df = df[pd.to_numeric(df["cycle"], errors="coerce").notna()].copy()
        df["cycle"] = df["cycle"].astype(int)
        return df.reset_index(drop=True)

    def _load_step(self):
        df = pd.read_excel(self._xl, sheet_name="Step Layer")
        df = df.rename(columns=STEP_RENAME)
        df = df[df["step_label"].notna()].copy()
        return df.reset_index(drop=True)

    def _load_record(self):
        df = pd.read_excel(self._xl, sheet_name="Record Layer")
        df = df.rename(columns=RECORD_RENAME)
        hdr = df["cycle_id"].apply(_is_bsmart_header)
        df  = df[~hdr].copy()
        df  = df[pd.to_numeric(df["cycle_id"], errors="coerce").notna()].copy()
        df["cycle_id"]    = df["cycle_id"].astype(int)
        df["step_id"]     = pd.to_numeric(df["step_id"],   errors="coerce")
        df["record_id"]   = pd.to_numeric(df["record_id"], errors="coerce")
        df["system_time"] = pd.to_datetime(df["system_time"], errors="coerce")
        t0 = df["system_time"].min()
        df["elapsed_s"] = (df["system_time"] - t0).dt.total_seconds()
        df["elapsed_h"] = df["elapsed_s"] / 3600.0
        df = self._build_cumulative(df)
        return df.reset_index(drop=True)

    def _build_cumulative(self, df):
        df = df.copy()
        df["cum_cap_Ah"] = 0.0
        df["cum_eng_Wh"] = 0.0
        off_cap = 0.0
        off_eng = 0.0
        for cid in sorted(df["cycle_id"].unique()):
            cm = df["cycle_id"] == cid
            for sid in sorted(df.loc[cm, "step_id"].dropna().unique()):
                sm  = cm & (df["step_id"] == sid)
                cap = pd.to_numeric(df.loc[sm, "step_cap_Ah"], errors="coerce").fillna(0.0)
                eng = pd.to_numeric(df.loc[sm, "step_eng_Wh"], errors="coerce").fillna(0.0)
                df.loc[sm, "cum_cap_Ah"] = off_cap + cap
                df.loc[sm, "cum_eng_Wh"] = off_eng + eng
                off_cap += float(cap.iloc[-1]) if len(cap) > 0 else 0.0
                off_eng += float(eng.iloc[-1]) if len(eng) > 0 else 0.0
        return df

    def _load_event(self):
        df = pd.read_excel(self._xl, sheet_name="Event")
        df = df.rename(columns=EVENT_RENAME)
        df = df[df["event_no"].notna()].copy()
        df = df[[c for c in df.columns if not str(c).startswith("Unnamed")]]
        return df.reset_index(drop=True)

    def _build_metadata(self):
        rec  = self.record_df
        c2   = rec[rec["cycle_id"] == CYCLE_MAIN]
        cyc2 = self.cycle_df[self.cycle_df["cycle"] == CYCLE_MAIN]
        chg_cap  = float(cyc2["chg_capacity_Ah"].iloc[0])  if len(cyc2) > 0 else 0.0
        dchg_cap = float(cyc2["dchg_capacity_Ah"].iloc[0]) if len(cyc2) > 0 else 0.0
        chg_e    = float(cyc2["chg_energy_Wh"].iloc[0])    if len(cyc2) > 0 else 0.0
        dchg_e   = float(cyc2["dchg_energy_Wh"].iloc[0])   if len(cyc2) > 0 else 0.0
        self.metadata = {
            "filename":        self.filepath.name,
            "test_id":         "INEVYD51105B0012",
            "test_profile":    "100% DOD B-SMART",
            "total_records":   len(rec),
            "total_cycles":    int(rec["cycle_id"].nunique()),
            "num_cells":       int(rec["num_cells"].dropna().iloc[0])
                               if rec["num_cells"].notna().any() else 16,
            "test_start":      rec["system_time"].min(),
            "test_end":        rec["system_time"].max(),
            "test_duration_h": (rec["system_time"].max()
                                - rec["system_time"].min()).total_seconds() / 3600,
            "chg_capacity_Ah":  chg_cap,
            "dchg_capacity_Ah": dchg_cap,
            "chg_energy_Wh":    chg_e,
            "dchg_energy_Wh":   dchg_e,
        }