import streamlit as st
import pandas as pd
import glob
from io import BytesIO

# ===================================
# PAGE SETTINGS
# ===================================

st.set_page_config(
    page_title="Latitude BOM Generator",
    layout="wide"
)

st.title("⚙️ LATITUDE BOM GENERATOR")

# ===================================
# HELPER FUNCTIONS
# ===================================

def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_value(value):
    """
    Generic cleaner for text values.
    """
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_config_id(value):
    """
    Converts Config IDs like:
    101.0 -> 101
    '101 ' -> 101
    'ABC001 ' -> ABC001
    """
    if pd.isna(value):
        return ""
    value = str(value).strip()
    if value.endswith(".0"):
        value = value[:-2]
    return value


def remove_pg(result_df, pg_number):
    return result_df[
        result_df["PG Number"].astype(str).str.strip() != str(pg_number).strip()
    ]


def add_pg_row(result_df, row_config_id, pg_number, description, quantity=1):
    new_row = pd.DataFrame([{
        "Config ID": row_config_id,
        "PG Number": pg_number,
        "Description": description,
        "Quantity": quantity
    }])
    return pd.concat([result_df, new_row], ignore_index=True)


def get_unique_values(df, column_name):
    if column_name not in df.columns:
        return []
    return sorted(
        df[column_name]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("nan", "")
        .loc[lambda s: s != ""]
        .unique()
        .tolist()
    )


# ===================================
# LOAD EXCEL
# ===================================

excel_files = glob.glob("*.xlsx")

if not excel_files:
    st.error("No Excel file found in this folder.")
    st.stop()

FILE_NAME = excel_files[0]

try:
    bom = pd.read_excel(FILE_NAME, sheet_name="BOM_Assistant")
    pg = pd.read_excel(FILE_NAME, sheet_name="PG_Mapping")
except Exception as e:
    st.error(f"Error while reading Excel file: {e}")
    st.stop()

bom.columns = bom.columns.str.strip()
pg.columns = pg.columns.str.strip()

# ===================================
# REQUIRED COLUMN CHECK
# ===================================

required_bom_columns = [
    "Config ID",
    "Pump Model",
    "Configuration",
    "Platform",
    "Dispenser Type",
    "Flow- UHF",
    "Motor Type"
]

required_pg_columns = [
    "Config ID",
    "PG Number",
    "Description",
    "Quantity"
]

missing_bom_cols = [c for c in required_bom_columns if c not in bom.columns]
missing_pg_cols = [c for c in required_pg_columns if c not in pg.columns]

if missing_bom_cols:
    st.error(f"Missing columns in BOM_Assistant sheet: {missing_bom_cols}")
    st.stop()

if missing_pg_cols:
    st.error(f"Missing columns in PG_Mapping sheet: {missing_pg_cols}")
    st.stop()

# ===================================
# CLEAN DATA
# ===================================

for df in [bom, pg]:
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype(str).str.strip()

bom["Config ID Key"] = bom["Config ID"].apply(normalize_config_id)
pg["Config ID Key"] = pg["Config ID"].apply(normalize_config_id)

pg["PG Number"] = pg["PG Number"].astype(str).str.strip()
pg["Description"] = pg["Description"].astype(str).str.strip()

# ===================================
# BASE CONFIGURATION - FULLY DYNAMIC
# ===================================

st.subheader("Base Configuration")

# Create a working copy for cascading filters
filtered_bom = bom.copy()

col1, col2 = st.columns(2)

# Pump Model
pump_model_options = get_unique_values(filtered_bom, "Pump Model")
with col1:
    pump_model = st.selectbox("Pump Model", pump_model_options, key="base_Pump Model")

filtered_bom = filtered_bom[
    filtered_bom["Pump Model"].astype(str).str.strip().str.lower()
    == str(pump_model).strip().lower()
]

# Configuration
configuration_options = get_unique_values(filtered_bom, "Configuration")
with col2:
    configuration = st.selectbox("Configuration", configuration_options, key="base_Configuration")

filtered_bom = filtered_bom[
    filtered_bom["Configuration"].astype(str).str.strip().str.lower()
    == str(configuration).strip().lower()
]

# Platform
platform_options = get_unique_values(filtered_bom, "Platform")
with col1:
    platform = st.selectbox("Platform", platform_options, key="base_Platform")

filtered_bom = filtered_bom[
    filtered_bom["Platform"].astype(str).str.strip().str.lower()
    == str(platform).strip().lower()
]

# Dispenser Type
dispenser_type_options = get_unique_values(filtered_bom, "Dispenser Type")
with col2:
    dispenser_type = st.selectbox("Dispenser Type", dispenser_type_options, key="base_Dispenser Type")

filtered_bom = filtered_bom[
    filtered_bom["Dispenser Type"].astype(str).str.strip().str.lower()
    == str(dispenser_type).strip().lower()
]

# Flow-UHF
flow_options = get_unique_values(filtered_bom, "Flow- UHF")
with col1:
    flow_uhf = st.selectbox("Flow- UHF", flow_options, key="base_Flow- UHF")

filtered_bom = filtered_bom[
    filtered_bom["Flow- UHF"].astype(str).str.strip().str.lower()
    == str(flow_uhf).strip().lower()
]

# Motor Type
motor_options = get_unique_values(filtered_bom, "Motor Type")
with col2:
    motor_type = st.selectbox("Motor Type", motor_options, key="base_Motor Type")

# Capture selected inputs
user_inputs = {
    "Pump Model": pump_model,
    "Configuration": configuration,
    "Platform": platform,
    "Dispenser Type": dispenser_type,
    "Flow- UHF": flow_uhf,
    "Motor Type": motor_type
}

# ===================================
# OPTIONAL FEATURES
# ===================================

st.subheader("Optional Features")

optional_features = [
    "Multimedia",
    "Multi PPU",
    "Printer",
    "Lighted Canopy",
    "VR Ready Kit",
    "VR Only",
    "Vapour Recovery +Monitoring",
    "IFSF",
    "Wide Gap Frame",
    "Hose Retraction"
]

feature_values = {}

col3, col4 = st.columns(2)

for i, feature in enumerate(optional_features):
    with (col3 if i % 2 == 0 else col4):
        feature_values[feature] = st.selectbox(
            feature,
            ["No", "Yes"],
            key=f"feature_{feature}"
        )

# ===================================
# PUMP STOP
# ===================================

pump_stop = st.selectbox(
    "Pump Stop",
    ["Yes", "No", "24VDC"],
    key="pump_stop"
)

# ===================================
# RETROFIT BRACKET AUTO-SET TO FS
# If ANY of the below is Yes, retrofit becomes FS
# ===================================

fs_trigger_features = [
    "Lighted Canopy",
    "Vapour Recovery +Monitoring",
    "Multimedia",
    "Multi PPU"
]

force_fs = any(feature_values[f] == "Yes" for f in fs_trigger_features) or (pump_stop == "24VDC")

if force_fs:
    st.info("Retrofit Bracket automatically set to FS based on selected options.")
    retrofit_bracket = "FS"
    st.selectbox(
        "Retrofit Bracket",
        ["FS"],
        key="retrofit_bracket",
        disabled=True
    )
else:
    retrofit_bracket = st.selectbox(
        "Retrofit Bracket",
        ["HS", "FS"],
        key="retrofit_bracket"
    )

# ===================================
# JUNCTION BOX
# ===================================

junction_box = st.selectbox(
    "Junction Box",
    ["Mains", "Horizon"],
    key="junction_box"
)

# =====================================
# FEATURE VALIDATION RULES
# =====================================

if feature_values["Multimedia"] == "Yes":
    feature_values["Multi PPU"] = "No"

invalid_multi_ppu_configs = [
    "2P2H4D",
    "2P4H4D",
    "3P6H4D",
    "4P8H4D"
]

if user_inputs["Configuration"] in invalid_multi_ppu_configs:
    feature_values["Multi PPU"] = "No"

# =====================================
# GENERATE BOM BUTTON
# =====================================

if st.button("Generate BOM"):

    # Use selected values to find the matching BOM_Assistant row
    filtered = bom.copy()

    for column_name in [
        "Pump Model",
        "Configuration",
        "Platform",
        "Dispenser Type",
        "Flow- UHF",
        "Motor Type"
    ]:
        filtered = filtered[
            filtered[column_name].astype(str).str.strip().str.lower()
            == str(user_inputs[column_name]).strip().lower()
        ]

    if filtered.empty:
        st.error("No matching configuration found in BOM_Assistant sheet.")
        with st.expander("Debug - Selected Inputs"):
            st.write(user_inputs)
        st.stop()

    config_id = filtered.iloc[0]["Config ID"]
    config_id_key = filtered.iloc[0]["Config ID Key"]

    # Find PG rows for this Config ID
    result = pg[
        pg["Config ID Key"].astype(str).str.strip()
        == str(config_id_key).strip()
    ].copy()

    if result.empty:
        st.error(f"No PG mapping found for Config ID: {config_id}")
        with st.expander("Debug - Config ID Mapping Issue"):
            st.write("Config ID from BOM_Assistant:", config_id)
            st.write("Normalized Config ID Key:", config_id_key)
            st.write("Available Config IDs in PG_Mapping:")
            st.write(pg["Config ID Key"].drop_duplicates().head(100).tolist())
        st.stop()

    # =====================================
    # FS / HS LOGIC
    # =====================================

    if retrofit_bracket == "FS":
        config_name = user_inputs["Configuration"]

        retrofit_rules = {
            "1P1H2D": ("PG6LM000055", "PG6LM000056", "Door Assembly for Mono_FS_Apollo MAX 4x4 KP"),
            "1P2H2D": ("PG6LM000065", "PG6LM000066", "Door Assembly for 1pmpd -FS - 4x4 Keypad"),
            "2P2H2D": ("PG6LM000065", "PG6LM000066", "Door Assembly for 1pmpd -FS - 4x4 Keypad"),
            "1P2H4D": ("PG6LM000063", "PG6LM000064", "Door Assembly for Duo_FS_Apollo MAX 4x4 KP"),
            "2P2H4D": ("PG6LM000063", "PG6LM000064", "Door Assembly for Duo_FS_ApolloMAX"),
            "2P4H2D": ("PG6LM000067", "PG6LM000068", "Door Assembly for 2PMPD -FS - 4x4 Keypad"),
            "3P6H2D": ("PG6LM000069", "PG6LM000070", "Door Assembly for 3pmpd -FS - 4x4 Keypad"),
            "4P8H2D": ("PG6LM000071", "PG6LM000072", "Door Assembly for 4PMPD -FS - 4x4 Keypad")
        }

        if config_name in retrofit_rules:
            old_pg, new_pg, new_desc = retrofit_rules[config_name]
            result = remove_pg(result, old_pg)
            result = add_pg_row(result, config_id, new_pg, new_desc, 1)

    # =====================================
    # PRINTER LOGIC
    # =====================================

    if feature_values["Printer"] == "Yes":
        if retrofit_bracket == "HS":
            printer_pg = "PGPL0000102"
            printer_desc = "Printer Assembly for Latitude-HS"
        else:
            printer_pg = "PGPL0000103"
            printer_desc = "Printer Assembly for Latitude_FS_MAX"

        result = add_pg_row(result, config_id, printer_pg, printer_desc, 1)

    # =====================================
    # IFSF LOGIC
    # =====================================

    if feature_values["IFSF"] == "Yes" and retrofit_bracket == "FS":
        result = add_pg_row(result, config_id, "PGPL0000104", "IFSF Interface for Latitude_MAX", 1)

    # =====================================
    # LIGHTED CANOPY LOGIC
    # =====================================

    if feature_values["Lighted Canopy"] == "Yes" and retrofit_bracket == "FS":

        vr_present = (
            feature_values["VR Ready Kit"] == "Yes"
            or feature_values["VR Only"] == "Yes"
            or feature_values["Vapour Recovery +Monitoring"] == "Yes"
        )

        result = remove_pg(result, "PG9T0000012")

        if user_inputs["Pump Model"] == "LS200":
            result = add_pg_row(result, config_id, "PG9C0000001", "Canopy Light for 2P - Latitude", 1)
            if not vr_present:
                result = add_pg_row(result, config_id, "PG9T0000020", "CDM-Din Rail Assembly (Base + Canopy) - Latitude", 1)

        elif user_inputs["Pump Model"] == "LS300":
            result = add_pg_row(result, config_id, "PG9C0000002", "Canopy Light for 4P - Latitude", 1)
            if not vr_present:
                result = add_pg_row(result, config_id, "PG9T0000020", "CDM-Din Rail Assembly (Base + Canopy) - Latitude", 1)

    # =====================================
    # VR READY KIT
    # =====================================

    if feature_values["VR Ready Kit"] == "Yes":
        result = remove_pg(result, "PG9T0000012")
        result = add_pg_row(result, config_id, "PG9T0000021", "CDM-Din Rail Assembly (Base +VRC) - Latitude", 1)

    # =====================================
    # VR ONLY LOGIC
    # =====================================

    if feature_values["VR Only"] == "Yes" and retrofit_bracket == "FS":
        result = remove_pg(result, "PG9T0000012")
        result = add_pg_row(result, config_id, "PG9V0000006", "Vapor Recovery System (VRC Only)", 1)
        result = add_pg_row(result, config_id, "PG9T0000021", "CDM-Din Rail Assembly (Base +VRC)", 1)

    # =====================================
    # VR + MONITORING LOGIC
    # =====================================

    if feature_values["Vapour Recovery +Monitoring"] == "Yes" and retrofit_bracket == "FS":
        result = remove_pg(result, "PG9T0000012")
        result = add_pg_row(result, config_id, "PG9V0000005", "Vapor Recovery System (VRC & VRM)", 1)
        result = add_pg_row(result, config_id, "PG9T0000021", "CDM-Din Rail Assembly (Base +VRC)", 1)

    # =====================================
    # MULTIMEDIA LOGIC
    # =====================================

    if feature_values["Multimedia"] == "Yes" and retrofit_bracket == "FS":

        multimedia_rules = {
            "1P1H2D": [
                ("PG6LM000030", "PG6LM000059", "MM ERA assembly for Mono/1PMPD - Latitude"),
                ("PG6LM000056", "PG6LM000079", "Multimedia Door Assembly for Mono")
            ],
            "1P2H2D": [
                ("PG6LM000030", "PG6LM000059", "MM ERA assembly for Mono/1PMPD - Latitude"),
                ("PG6LM000066", "PG6LM000081", "Multimedia Door Assembly for 1pmpd")
            ],
            "2P2H2D": [
                ("PG6LM000046", "PG6LM000060", "MM ERA assembly for Duo/2PMPD"),
                ("PG6LM000066", "PG6LM000081", "Multimedia Door Assembly for 1pmpd")
            ],
            "1P2H4D": [
                ("PG6LM000030", "PG6LM000059", "MM ERA assembly for Mono/1PMPD"),
                ("PG6LM000064", "PG6LM000080", "Multimedia Door Assembly for Duo")
            ],
            "2P4H2D": [
                ("PG6LM000046", "PG6LM000060", "MM ERA assembly for Duo/2PMPD"),
                ("PG6LM000068", "PG6LM000082", "Multimedia Door Assembly for 2PMPD")
            ],
            "3P6H2D": [
                ("PG6LM000033", "PG6LM000061", "MM ERA assembly for 3pmpd"),
                ("PG6LM000070", "PG6LM000083", "Multimedia Door Assembly for 3pmpd")
            ],
            "4P8H2D": [
                ("PG6LM000035", "PG6LM000062", "MM ERA assembly for 4PMPD"),
                ("PG6LM000072", "PG6LM000084", "Multimedia Door Assembly for 4PMPD")
            ]
        }

        config_name = user_inputs["Configuration"]

        if config_name in multimedia_rules:
            for old_pg, new_pg, desc in multimedia_rules[config_name]:
                result = remove_pg(result, old_pg)
                result = add_pg_row(result, config_id, new_pg, desc, 1)

    # =====================================
    # MULTI PPU LOGIC
    # =====================================

    if feature_values["Multi PPU"] == "Yes" and retrofit_bracket == "FS":

        multi_ppu_rules = {
            "1P2H2D": ("PG6LM000066", "PG6LM000088", "Door Assembly-Multi PPU Display-1PMPD_FS"),
            "2P4H2D": ("PG6LM000068", "PG6LM000089", "Door Assembly-Multi PPU Display-2PMPD_FS"),
            "3P6H2D": ("PG6LM000070", "PG6LM000090", "Door Assembly-Multi PPU Display-3PMPD_FS"),
            "4P8H2D": ("PG6LM000072", "PG6LM000091", "Door Assembly-Multi PPU Display-4PMPD_FS")
        }

        config_name = user_inputs["Configuration"]

        if config_name in multi_ppu_rules:
            old_pg, new_pg, desc = multi_ppu_rules[config_name]
            result = remove_pg(result, old_pg)
            result = add_pg_row(result, config_id, new_pg, desc, 1)

    # =====================================
    # JUNCTION BOX HORIZON LOGIC
    # =====================================

    if junction_box == "Horizon":
        vr_present = (
            feature_values["VR Ready Kit"] == "Yes"
            or feature_values["VR Only"] == "Yes"
            or feature_values["Vapour Recovery +Monitoring"] == "Yes"
        )

        config_name = user_inputs["Configuration"]
        disp_type = clean_text(user_inputs["Dispenser Type"]).lower()

        result = remove_pg(result, "PG8L0000101")

        if vr_present and disp_type == "suction":

            horizon_vr_rules = {
                "1P1H2D": ("PG8L0000038", "PG8L0000062", "Horizon Jun.Box 1P_SUCTION 2W Communication cable - Latitude (With VR)"),
                "1P2H2D": ("PG8L0000038", "PG8L0000062", "Horizon Jun.Box 1P_SUCTION 2W Communication cable - Latitude (With VR)"),
                "2P4H2D": ("PG8L0000038", "PG8L0000063", "Horizon Jun.Box 2P_SUCTION 2W Communication cable - Latitude (With VR)"),
                "2P2H4D": ("PG8L0000038", "PG8L0000063", "Horizon Jun.Box 2P_SUCTION 2W Communication cable - Latitude (With VR)"),
                "2P4H4D": ("PG8L0000038", "PG8L0000063", "Horizon Jun.Box 2P_SUCTION 2W Communication cable - Latitude (With VR)"),
                "3P6H2D": ("PG8L0000038", "PG8L0000064", "Horizon Jun.Box 3P_SUCTION 2W Communication cable - Latitude (With VR)"),
                "3P6H4D": ("PG8L0000038", "PG8L0000064", "Horizon Jun.Box 3P_SUCTION 2W Communication cable - Latitude (With VR)")
            }

            if config_name in horizon_vr_rules:
                old_pg, new_pg, desc = horizon_vr_rules[config_name]
                result = remove_pg(result, old_pg)
                result = add_pg_row(result, config_id, new_pg, desc, 1)

        else:
            horizon_rules = {
                ("1P1H2D", "suction"): ("PG8L0000030", "PG8L0000043", "Horizon Jun.Box 1P_SUCTION 2W Communication cable - Latitude"),
                ("1P1H2D", "pressure"): ("PG8L0000044", "PG8L0000026", "Horizon Jun.Box 1P_PRESSURE 2W Communication cable - Latitude"),
                ("1P2H2D", "suction"): ("PG8L0000030", "PG8L0000043", "Horizon Jun.Box 1P_SUCTION 2W Communication cable - Latitude"),
                ("1P2H2D", "pressure"): ("PG8L0000044", "PG8L0000026", "Horizon Jun.Box 1P_PRESSURE 2W Communication cable - Latitude"),
                ("1P2H4D", "suction"): ("PG8L0000030", "PG8L0000043", "Horizon Jun.Box 1P_SUCTION 2W Communication cable - Latitude"),
                ("1P2H4D", "pressure"): ("PG8L0000044", "PG8L0000026", "Horizon Jun.Box 1P_PRESSURE 2W Communication cable - Latitude"),
                ("2P4H2D", "suction"): ("PG8L0000031", "PG8L0000042", "Horizon Jun.Box 2P_SUCTION 2W Communication cable - Latitude"),
                ("2P4H2D", "pressure"): ("PG8L0000045", "PG8L0000019", "Horizon Jun.Box 2P_PRESSURE 2W Communication cable - Latitude"),
                ("2P2H2D", "pressure"): ("PG8L0000045", "PG8L0000019", "Horizon Jun.Box 2P_PRESSURE 2W Communication cable - Latitude"),
                ("2P2H4D", "suction"): ("PG8L0000031", "PG8L0000042", "Horizon Jun.Box 2P_SUCTION 2W Communication cable - Latitude"),
                ("2P2H4D", "pressure"): ("PG8L0000045", "PG8L0000019", "Horizon Jun.Box 2P_PRESSURE 2W Communication cable - Latitude"),
                ("3P6H2D", "suction"): ("PG8L0000032", "PG8L0000052", "Horizon Jun.Box 3P_SUCTION 2W Communication cable - Latitude"),
                ("3P6H2D", "pressure"): ("PG8L0000046", "PG8L0000017", "Horizon Jun.Box 3P_PRESSURE 2W communication - Latitude"),
                ("4P8H2D", "pressure"): ("PG8L0000047", "PG8L0000018", "Horizon Jun.Box 4P_PRESSURE 2W communication - Latitude")
            }

            key = (config_name, disp_type)

            if key in horizon_rules:
                old_pg, new_pg, desc = horizon_rules[key]
                result = remove_pg(result, old_pg)
                result = add_pg_row(result, config_id, new_pg, desc, 1)

    # =====================================
    # PUMP STOP LOGIC
    # =====================================

    if pump_stop == "No":
        result = remove_pg(result, "PG9S0000007")
        result = add_pg_row(result, config_id, "LF911190015", "0.75sq.mm Black Shorting cable_100mm", 1)
        result = add_pg_row(result, config_id, "LF911190014", "0.75sq.mm Red Shorting cable_100mm", 1)

    # =====================================
    # PUMP STOP 24VDC LOGIC
    # =====================================

    if pump_stop == "24VDC":

        config_name = user_inputs["Configuration"]

        multimedia_present = feature_values["Multimedia"] == "Yes"

        vr_present = (
            feature_values["VR Ready Kit"] == "Yes"
            or feature_values["VR Only"] == "Yes"
            or feature_values["Vapour Recovery +Monitoring"] == "Yes"
        )

        result = result[
            ~result["PG Number"].astype(str).str.strip().isin([
                "PG9T0000012",
                "PG9T0000020",
                "PG9T0000021",
                "PG9T0000036",
                "PG9T0000037"
            ])
        ]

        if multimedia_present:
            mm_24v_rules = {
                "1P1H2D": ("PG6LM000059", "PG6LM000051", "MM ERA assembly for Mono/1PMPD - Latitude -24VDC"),
                "1P2H2D": ("PG6LM000059", "PG6LM000051", "MM ERA assembly for Mono/1PMPD - Latitude -24VDC"),
                "1P2H4D": ("PG6LM000059", "PG6LM000051", "MM ERA assembly for Mono/1PMPD - Latitude -24VDC"),
                "2P2H2D": ("PG6LM000060", "PG6LM000052", "MM ERA assembly for Duo/2PMPD - Latitude -24VDC"),
                "2P4H2D": ("PG6LM000060", "PG6LM000052", "MM ERA assembly for Duo/2PMPD - Latitude -24VDC"),
                "2P2H4D": ("PG6LM000060", "PG6LM000052", "MM ERA assembly for Duo/2PMPD - Latitude -24VDC"),
                "3P6H2D": ("PG6LM000061", "PG6LM000053", "MM ERA assembly for 3pmpd - Latitude -24VDC"),
                "4P8H2D": ("PG6LM000062", "PG6LM000054", "MM ERA assembly for 4PMPD - Latitude -24VDC")
            }

            if config_name in mm_24v_rules:
                old_pg, new_pg, desc = mm_24v_rules[config_name]
                result = remove_pg(result, old_pg)
                result = add_pg_row(result, config_id, new_pg, desc, 1)

        else:
            era_rules = {
                "1P1H2D": ("PG6LM000030", "PG6LM000043", "ERA assembly for Mono/1PMPD-24VDC-Latitude"),
                "1P2H2D": ("PG6LM000030", "PG6LM000043", "ERA assembly for Mono/1PMPD-24VDC-Latitude"),
                "1P2H4D": ("PG6LM000030", "PG6LM000043", "ERA assembly for Mono/1PMPD-24VDC-Latitude"),
                "2P2H2D": ("PG6LM000046", "PG6LM000044", "ERA assembly for Duo/2PMPD-24VDC-Latitude"),
                "2P4H2D": ("PG6LM000046", "PG6LM000044", "ERA assembly for Duo/2PMPD-24VDC-Latitude"),
                "2P2H4D": ("PG6LM000046", "PG6LM000044", "ERA assembly for Duo/2PMPD-24VDC-Latitude"),
                "3P6H2D": ("PG6LM000033", "PG6LM000034", "ERA ASM 3PMPD-DC Stop Apollo MAX-FS"),
                "4P8H2D": ("PG6LM000035", "PG6LM000048", "ERA ASM for 4PMPD-DC Stop Apollo MAX")
            }

            if config_name in era_rules:
                old_pg, new_pg, desc = era_rules[config_name]
                result = remove_pg(result, old_pg)
                result = add_pg_row(result, config_id, new_pg, desc, 1)

        result = remove_pg(result, "PG9S0000007")
        result = remove_pg(result, "PG9S0000009")

        if vr_present:
            switch_pg = "PG9S0000013"
            switch_desc = "24V DC Emg Switch Assembly (Base +VRC+24V DC) - Latitude"
        else:
            switch_pg = "PG9S0000009"
            switch_desc = "24V DC Emg Switch Assembly for Latitude"

        result = add_pg_row(result, config_id, switch_pg, switch_desc, 1)

    # =====================================
    # WIRE GUIDE & BELT QUANTITY LOGIC
    # =====================================

    base_qty = 17 if retrofit_bracket == "FS" else 13

    extra_qty = 0
    if feature_values["Lighted Canopy"] == "Yes":
        extra_qty += 7
    if feature_values["Printer"] == "Yes":
        extra_qty += 1
    if feature_values["Multimedia"] == "Yes":
        extra_qty += 5
    if feature_values["Vapour Recovery +Monitoring"] == "Yes":
        extra_qty += 3

    final_qty = base_qty + extra_qty

    mask_wire = result["PG Number"].astype(str).str.strip() == "GL50021"
    if mask_wire.any():
        result.loc[mask_wire, "Quantity"] = final_qty

    mask_belt = result["PG Number"].astype(str).str.strip() == "GL50064"
    if mask_belt.any():
        result.loc[mask_belt, "Quantity"] = final_qty

    # =====================================
    # FINAL CLEANUP
    # =====================================

    result["PG Number"] = result["PG Number"].astype(str).str.strip()
    result["Description"] = result["Description"].astype(str).str.strip()

    result = result.drop_duplicates(subset=["PG Number"], keep="last")

    if result.empty:
        st.error("BOM result is empty after applying rules.")
        st.stop()

    final_bom = result[["PG Number", "Description", "Quantity"]].copy()

    st.success(f"BOM Generated Successfully — Config ID: {config_id}")
    st.write(f"**Total PG rows:** {len(final_bom)}")

    st.dataframe(final_bom, hide_index=True, use_container_width=True)

    # =====================================
    # DOWNLOAD EXCEL
    # =====================================

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        final_bom.to_excel(writer, sheet_name="Generated_BOM", index=False)

    output.seek(0)

    st.download_button(
        label="📥 Download BOM Excel",
        data=output.getvalue(),
        file_name="Generated_BOM.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
