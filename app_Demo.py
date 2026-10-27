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
# LOAD EXCEL
# ===================================

excel_files = glob.glob("*.xlsx")

if not excel_files:
    st.error("No Excel file found")
    st.stop()

FILE_NAME = excel_files[0]

bom = pd.read_excel(
    FILE_NAME,
    sheet_name="BOM_Assistant"
)

pg = pd.read_excel(
    FILE_NAME,
    sheet_name="PG_Mapping"
)

bom.columns = bom.columns.str.strip()
pg.columns = pg.columns.str.strip()

# ===================================
# BASE CONFIGURATION
# ===================================

st.subheader("Base Configuration")

base_columns = [
    "Pump Model",
    "Configuration",
    "Platform",
    "Dispenser Type",
    "Flow- UHF",
    "Motor Type"
]

# ===================================
# ALL CONFIGURATIONS
# ===================================

all_configurations = [
    "1P1H1D",
    "1P1H2D",
    "1P2H2D",
    "1P2H4D",
    "2P2H2D",
    "2P2H4D",
    "2P4H2D",
    "2P4H4D",
    "3P6H2D",
    "3P6H4D",
    "4P8H2D",
    "4P8H4D"
]

# LS100 / LS200 → only upto 2P
configurations_upto_2p = [
    "1P1H1D",
    "1P1H2D",
    "1P2H2D",
    "1P2H4D",
    "2P2H2D",
    "2P2H4D",
    "2P4H2D",
    "2P4H4D"
]

user_inputs = {}

col1, col2 = st.columns(2)

for i, column_name in enumerate(base_columns):

    if column_name == "Configuration":

        # LS300 → all configurations
        # LS100 / LS200 → only upto 2P
        selected_pump = user_inputs.get("Pump Model", "")

        if selected_pump == "LS300":
            values = all_configurations
        else:
            values = configurations_upto_2p

    elif column_name == "Motor Type":

        dispenser_type = str(user_inputs.get("Dispenser Type", "")).strip().lower()

        if dispenser_type == "pressure":
            values = ["No"]

        elif dispenser_type == "suction":
            values = ["1PH", "3PH"]

        else:
            values = sorted(
                bom[column_name]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

    else:
        values = sorted(
            bom[column_name]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    if not values:
        values = [""]

    target_col = col1 if i % 2 == 0 else col2

    with target_col:
        user_inputs[column_name] = st.selectbox(
            column_name,
            values,
            key=f"base_{column_name}"
        )

# ===================================
# OPTIONAL FEATURES
# ===================================

st.subheader("Optional Features")

# ===================================
# OPTIONAL FEATURES WITH
# MULTIMEDIA <-> MULTI PPU EXCLUSION
# ===================================

feature_values = {}

col3, col4 = st.columns(2)

# Render Multimedia first
with col3:
    multimedia_val = st.selectbox(
        "Multimedia",
        ["No", "Yes"],
        key="feature_Multimedia"
    )
    feature_values["Multimedia"] = multimedia_val

# Multi PPU — only shows No if Multimedia = Yes
with col4:
    if multimedia_val == "Yes":
        multi_ppu_val = st.selectbox(
            "Multi PPU",
            ["No"],
            key="feature_Multi PPU",
            disabled=True,
            help="Not available when Multimedia is selected."
        )
    else:
        multi_ppu_val = st.selectbox(
            "Multi PPU",
            ["No", "Yes"],
            key="feature_Multi PPU"
        )
    feature_values["Multi PPU"] = multi_ppu_val

# If Multi PPU = Yes → force Multimedia = No internally
if multi_ppu_val == "Yes":
    feature_values["Multimedia"] = "No"

# ===================================
# REMAINING OPTIONAL FEATURES
# LS100 → Lighted Canopy disabled
# ===================================

remaining_optional = [
    "Printer",
    "Lighted Canopy",
    "VR Ready Kit",
    "VR Only",
    "Vapour Recovery +Monitoring",
    "IFSF",
    "Wide Gap Frame",
    "Hose Retraction"
]

for i, feature in enumerate(remaining_optional):
    target_col = col3 if i % 2 == 0 else col4

    with target_col:

        # LS100 → Lighted Canopy = No, disabled
        if feature == "Lighted Canopy" and user_inputs.get("Pump Model") == "LS100":
            feature_values[feature] = st.selectbox(
                feature,
                ["No"],
                key=f"feature_{feature}",
                disabled=True,
                help="Lighted Canopy is not applicable for LS100."
            )
        else:
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
# AUTO FORCE RETROFIT TO FS
# If ANY of these = Yes → FS only
# HS not shown in dropdown
# ===================================

fs_trigger_features = [
    "Lighted Canopy",
    "Vapour Recovery +Monitoring",
    "Multimedia",
    "Multi PPU"
]

force_fs = (
    any(feature_values[f] == "Yes" for f in fs_trigger_features)
    or pump_stop == "24VDC"
)

if force_fs:
    st.info("🔒 Retrofit Bracket automatically set to FS based on selected options.")
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
    st.warning("Multi PPU is not supported for this configuration.")

fs_only_features = [
    "Lighted Canopy",
    "Vapour Recovery +Monitoring",
    "Multimedia",
    "Multi PPU"
]

if retrofit_bracket == "HS":
    for feature in fs_only_features:
        if feature in feature_values:
            feature_values[feature] = "No"

    if pump_stop == "24VDC":
        pump_stop = "Yes"

    st.info(
        "Lighted Canopy, VR Monitoring, Multimedia, 24VDC Stop and Multi PPU are supported only for FS."
    )

# =====================================
# GENERATE BOM BUTTON
# =====================================

if st.button("Generate BOM"):

    filtered = bom.copy()

    for column_name in base_columns:
        filtered = filtered[
            filtered[column_name].astype(str).str.strip()
            == str(user_inputs[column_name]).strip()
        ]

    if filtered.empty:
        st.error("No matching configuration found")

    else:
        config_id = filtered.iloc[0]["Config ID"]

        result = pg[pg["Config ID"] == config_id].copy()

        # =====================================
        # RETROFIT BRACKET LOGIC
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

                result = result[
                    result["PG Number"].astype(str).str.strip() != old_pg
                ]

                replace_row = pd.DataFrame([{
                    "Config ID": config_id,
                    "PG Number": new_pg,
                    "Description": new_desc,
                    "Quantity": 1
                }])

                result = pd.concat([result, replace_row], ignore_index=True)

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

            printer_row = pd.DataFrame([{
                "Config ID": config_id,
                "PG Number": printer_pg,
                "Description": printer_desc,
                "Quantity": 1
            }])

            result = pd.concat([result, printer_row], ignore_index=True)

        # =====================================
        # IFSF LOGIC
        # =====================================

        if feature_values["IFSF"] == "Yes" and retrofit_bracket == "FS":

            IFSF_row = pd.DataFrame([{
                "Config ID": config_id,
                "PG Number": "PGPL0000104",
                "Description": "IFSF Interface for Latitude_MAX",
                "Quantity": 1
            }])

            result = pd.concat([result, IFSF_row], ignore_index=True)

        # =====================================
        # LIGHTED CANOPY LOGIC
        # =====================================

        if feature_values["Lighted Canopy"] == "Yes" and retrofit_bracket == "FS":

            vr_present = (
                feature_values["VR Ready Kit"] == "Yes"
                or feature_values["VR Only"] == "Yes"
                or feature_values["Vapour Recovery +Monitoring"] == "Yes"
            )

            result = result[
                result["PG Number"].astype(str).str.strip() != "PG9T0000012"
            ]

            canopy_data = []

            if user_inputs["Pump Model"] == "LS200":
                canopy_data.append({
                    "Config ID": config_id,
                    "PG Number": "PG9C0000001",
                    "Description": "Canopy Light for 2P - Latitude",
                    "Quantity": 1
                })

                if not vr_present:
                    canopy_data.append({
                        "Config ID": config_id,
                        "PG Number": "PG9T0000020",
                        "Description": "CDM-Din Rail Assembly (Base + Canopy) - Latitude",
                        "Quantity": 1
                    })

            elif user_inputs["Pump Model"] == "LS300":
                canopy_data.append({
                    "Config ID": config_id,
                    "PG Number": "PG9C0000002",
                    "Description": "Canopy Light for 4P - Latitude",
                    "Quantity": 1
                })

                if not vr_present:
                    canopy_data.append({
                        "Config ID": config_id,
                        "PG Number": "PG9T0000020",
                        "Description": "CDM-Din Rail Assembly (Base + Canopy) - Latitude",
                        "Quantity": 1
                    })

            if canopy_data:
                canopy_rows = pd.DataFrame(canopy_data)
                result = pd.concat([result, canopy_rows], ignore_index=True)

        # =====================================
        # VR READY KIT
        # =====================================

        if feature_values["VR Ready Kit"] == "Yes":

            result = result[
                result["PG Number"].astype(str).str.strip() != "PG9T0000012"
            ]

            vr_row = pd.DataFrame([{
                "Config ID": config_id,
                "PG Number": "PG9T0000021",
                "Description": "CDM-Din Rail Assembly (Base +VRC) - Latitude",
                "Quantity": 1
            }])

            result = pd.concat([result, vr_row], ignore_index=True)

        # =====================================
        # VR ONLY LOGIC
        # =====================================

        if feature_values["VR Only"] == "Yes" and retrofit_bracket == "FS":

            result = result[
                result["PG Number"].astype(str).str.strip() != "PG9T0000012"
            ]

            vr_only_rows = pd.DataFrame([
                {
                    "Config ID": config_id,
                    "PG Number": "PG9V0000006",
                    "Description": "Vapor Recovery System (VRC Only)",
                    "Quantity": 1
                },
                {
                    "Config ID": config_id,
                    "PG Number": "PG9T0000021",
                    "Description": "CDM-Din Rail Assembly (Base +VRC)",
                    "Quantity": 1
                }
            ])

            result = pd.concat([result, vr_only_rows], ignore_index=True)

        # =====================================
        # VR + MONITORING LOGIC
        # =====================================

        if feature_values["Vapour Recovery +Monitoring"] == "Yes" and retrofit_bracket == "FS":

            result = result[
                result["PG Number"].astype(str).str.strip() != "PG9T0000012"
            ]

            vr_monitor_rows = pd.DataFrame([
                {
                    "Config ID": config_id,
                    "PG Number": "PG9V0000005",
                    "Description": "Vapor Recovery System (VRC & VRM)",
                    "Quantity": 1
                },
                {
                    "Config ID": config_id,
                    "PG Number": "PG9T0000021",
                    "Description": "CDM-Din Rail Assembly (Base +VRC)",
                    "Quantity": 1
                }
            ])

            result = pd.concat([result, vr_monitor_rows], ignore_index=True)

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

                    result = result[
                        result["PG Number"].astype(str).str.strip() != old_pg
                    ]

                    add_row = pd.DataFrame([{
                        "Config ID": config_id,
                        "PG Number": new_pg,
                        "Description": desc,
                        "Quantity": 1
                    }])

                    result = pd.concat([result, add_row], ignore_index=True)

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

                result = result[
                    result["PG Number"].astype(str).str.strip() != old_pg
                ]

                add_row = pd.DataFrame([{
                    "Config ID": config_id,
                    "PG Number": new_pg,
                    "Description": desc,
                    "Quantity": 1
                }])

                result = pd.concat([result, add_row], ignore_index=True)

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
            disp_type = str(user_inputs["Dispenser Type"]).strip().lower()

            result = result[
                result["PG Number"].astype(str).str.strip() != "PG8L0000101"
            ]

            # =====================================
            # HORIZON INSTALLATION KIT REPLACEMENT
            # =====================================

            # ST75058 → just remove, no replacement
            result = result[
                result["PG Number"].astype(str).str.strip() != "ST75058"
            ]

            horizon_install_replace = {
                "ST75056": "ST75059",
                "ST75057": "ST75060",
                "ST75055": "ST75061",
                "ST75043": "ST75035",
                "ST75044": "ST75036",
                "ST75045": "ST75037",
                "ST75046": "ST75038"
            }

            for old_install_pg, new_install_pg in horizon_install_replace.items():
                mask = (
                    result["PG Number"].astype(str).str.strip() == old_install_pg
                )
                if mask.any():
                    existing_desc = result.loc[mask, "Description"].values[0]
                    existing_qty  = result.loc[mask, "Quantity"].values[0]

                    result = result[
                        result["PG Number"].astype(str).str.strip() != old_install_pg
                    ]

                    replace_row = pd.DataFrame([{
                        "Config ID":   config_id,
                        "PG Number":   new_install_pg,
                        "Description": existing_desc,
                        "Quantity":    existing_qty
                    }])

                    result = pd.concat([result, replace_row], ignore_index=True)

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

                    result = result[
                        result["PG Number"].astype(str).str.strip() != old_pg
                    ]

                    horizon_row = pd.DataFrame([{
                        "Config ID": config_id,
                        "PG Number": new_pg,
                        "Description": desc,
                        "Quantity": 1
                    }])

                    result = pd.concat([result, horizon_row], ignore_index=True)

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

                    result = result[
                        result["PG Number"].astype(str).str.strip() != old_pg
                    ]

                    horizon_row = pd.DataFrame([{
                        "Config ID": config_id,
                        "PG Number": new_pg,
                        "Description": desc,
                        "Quantity": 1
                    }])

                    result = pd.concat([result, horizon_row], ignore_index=True)

        # =====================================
        # PUMP STOP LOGIC
        # =====================================

        if pump_stop == "No":

            result = result[
                result["PG Number"].astype(str).str.strip() != "PG9S0000007"
            ]

            pump_stop_rows = pd.DataFrame([
                {
                    "Config ID": config_id,
                    "PG Number": "LF911190015",
                    "Description": "0.75sq.mm Black Shorting cable_100mm",
                    "Quantity": 1
                },
                {
                    "Config ID": config_id,
                    "PG Number": "LF911190014",
                    "Description": "0.75sq.mm Red Shorting cable_100mm",
                    "Quantity": 1
                }
            ])

            result = pd.concat([result, pump_stop_rows], ignore_index=True)

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

                    result = result[
                        result["PG Number"].astype(str).str.strip() != old_pg
                    ]

                    era_row = pd.DataFrame([{
                        "Config ID": config_id,
                        "PG Number": new_pg,
                        "Description": desc,
                        "Quantity": 1
                    }])

                    result = pd.concat([result, era_row], ignore_index=True)

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

                    result = result[
                        result["PG Number"].astype(str).str.strip() != old_pg
                    ]

                    era_row = pd.DataFrame([{
                        "Config ID": config_id,
                        "PG Number": new_pg,
                        "Description": desc,
                        "Quantity": 1
                    }])

                    result = pd.concat([result, era_row], ignore_index=True)

            result = result[
                result["PG Number"].astype(str).str.strip() != "PG9S0000007"
            ]

            result = result[
                result["PG Number"].astype(str).str.strip() != "PG9S0000009"
            ]

            if vr_present:
                switch_pg = "PG9S0000013"
                switch_desc = "24V DC Emg Switch Assembly (Base +VRC+24V DC) - Latitude"
            else:
                switch_pg = "PG9S0000009"
                switch_desc = "24V DC Emg Switch Assembly for Latitude"

            switch_row = pd.DataFrame([{
                "Config ID": config_id,
                "PG Number": switch_pg,
                "Description": switch_desc,
                "Quantity": 1
            }])

            result = pd.concat([result, switch_row], ignore_index=True)

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

        mask_wire = (
            result["PG Number"].astype(str).str.strip() == "GL50021"
        )

        if mask_wire.any():
            result.loc[mask_wire, "Quantity"] = final_qty

        mask_belt = (
            result["PG Number"].astype(str).str.strip() == "GL50064"
        )

        if mask_belt.any():
            result.loc[mask_belt, "Quantity"] = final_qty

        # =====================================
        # WIDE GAP FRAME WARNING
        # =====================================

        if feature_values["Wide Gap Frame"] == "Yes":
            st.warning(
                "⚠ Wide Gap Frame = Yes. Corresponding Junction Box PG replacement is required based on Configuration and Dispenser Type."
            )

        # =====================================
        # HOSE RETRACTION WARNING
        # =====================================

        if feature_values["Hose Retraction"] == "Yes":
            st.warning(
                "⚠ Hose Retraction selected. Replace Pulser PG based on Configuration and add Hose Retraction PGs as per Master Sheet."
            )

        # =====================================
        # FINAL CLEANUP
        # =====================================

        result = result.drop_duplicates(
            subset=["PG Number"],
            keep="last"
        )

        # =====================================
        # FINAL BOM
        # =====================================

        final_bom = result[["PG Number", "Description", "Quantity"]]

        st.success(f"BOM Generated Successfully - Config ID {config_id}")

        st.dataframe(
            final_bom,
            hide_index=True,
            use_container_width=True
        )

        # =====================================
        # DOWNLOAD EXCEL
        # =====================================

        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            final_bom.to_excel(
                writer,
                sheet_name="Generated_BOM",
                index=False
            )

        output.seek(0)

        st.download_button(
            label="📥 Download BOM Excel",
            data=output.getvalue(),
            file_name="Generated_BOM.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
