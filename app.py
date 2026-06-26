#!/usr/bin/env python3
"""
DatAnalyzer Streamlit UI.

Launch with:
    streamlit run app.py
"""

import os
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from datanalyzer.part1_raw_data_handling import load_raw_mea_data_to_Data_and_DataInfo
from datanalyzer.part2_peak_handling import find_peaks_in_loop, set_default_filetype_rules_for_peak_finding
from datanalyzer.part3_data_handling_and_analyses import update_Data_BPM, create_BPM_summary
from datanalyzer.part4_export import export_to_duckdb
from datanalyzer.part5_report import generate_html_report


st.set_page_config(page_title="DatAnalyzer", layout="wide")
st.title("DatAnalyzer — MEA Field Potential Analysis")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Parameters")

    folder = st.text_input("H5 folder path", placeholder=r"C:\path\to\h5\files")

    with st.expander("Experiment info"):
        exp_name  = st.text_input("Experiment name",  value="MEA2020_03_02")
        meas_name = st.text_input("Measurement name", value="MEA21002b")
        meas_date = st.text_input("Measurement date", value="2020_03_02")

    electrodes_str = st.text_input("Electrode numbers (space-separated)", value="71 84")
    max_bpm    = st.number_input("Max BPM",            value=40.0,  min_value=1.0, max_value=300.0, step=5.0)
    min_peak_v = st.number_input("Min peak value (V)", value=5e-5,  format="%.2e", step=1e-5)

    run_btn = st.button("Run Analysis", type="primary", use_container_width=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def _parse_electrodes(s: str):
    try:
        return [int(x) for x in s.split()]
    except ValueError:
        return None


def _file_labels(DataInfo, n_files: int):
    if DataInfo.file_names:
        return [os.path.basename(fn) for fn in DataInfo.file_names]
    return [f"File {i + 1}" for i in range(n_files)]


def _line_fig(data: np.ndarray, file_labels, electrodes, title: str, ylabel: str):
    fig, ax = plt.subplots(figsize=(8, 3.5))
    x = range(len(file_labels))
    for ci, elec in enumerate(electrodes):
        if ci >= data.shape[1]:
            break
        ax.plot(x, data[:, ci], marker="o", linewidth=1.5, markersize=4, label=f"E{elec}")
    ax.set_xticks(list(x))
    ax.set_xticklabels(file_labels, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.legend(fontsize=8, ncol=max(1, len(electrodes) // 6))
    ax.grid(True, alpha=0.25, linestyle="--")
    plt.tight_layout()
    return fig


def _summary_df(DataInfo, summary: dict) -> pd.DataFrame:
    n_files = DataInfo.files_amount
    labels = _file_labels(DataInfo, n_files)
    electrodes = DataInfo.MEA_electrode_numbers
    rows = []
    for fi, flabel in enumerate(labels):
        for ci, elec in enumerate(electrodes):
            if ci >= summary["BPM_avg"].shape[1]:
                break
            def _v(key, scale=1.0):
                v = summary[key][fi, ci]
                return round(float(v) * scale, 3) if not np.isnan(v) else None
            rows.append({
                "File":         flabel,
                "Electrode":    elec,
                "Peaks":        int(summary["Amount_of_peaks"][fi, ci]) if not np.isnan(summary["Amount_of_peaks"][fi, ci]) else None,
                "BPM avg":      _v("BPM_avg"),
                "BPM CV%":      _v("BPM_avg_stdpros"),
                "Amp avg (µV)": _v("Amplitude_avg", 1e6),
                "Amp CV%":      _v("Amplitude_std_pros"),
            })
    return pd.DataFrame(rows)


# ── Run analysis ──────────────────────────────────────────────────────────────
if run_btn:
    electrodes = _parse_electrodes(electrodes_str)

    if not folder or not os.path.isdir(folder):
        st.error("Please provide a valid folder path containing .h5 files.")
    elif not electrodes:
        st.error("Could not parse electrode numbers — use space-separated integers, e.g. '71 84'.")
    else:
        with st.spinner("Loading data…"):
            Data, DataInfo = load_raw_mea_data_to_Data_and_DataInfo(
                exp_name=exp_name,
                meas_name=meas_name,
                meas_date=meas_date,
                file_type=".h5",
                folder_of_files=folder,
                manually_chosen_mea_electrodes=electrodes,
            )

        if not Data:
            st.error("No .h5 files found in the given folder.")
        else:
            with st.spinner("Finding peaks and computing BPM…"):
                Rule = set_default_filetype_rules_for_peak_finding(
                    frame_rate=float(DataInfo.framerate.flat[0])
                )
                Rule.max_bpm = max_bpm
                Rule.min_peak_value = min_peak_v
                DataInfo.Rule = Rule

                Data_BPM = find_peaks_in_loop(Data, DataInfo, Rule_in=Rule, data_multiply=-1)
                Data_BPM = update_Data_BPM(DataInfo, Data_BPM, using_high_peaks=-1)
                Data_BPM_summary = create_BPM_summary(DataInfo, Data_BPM)

            # Pre-generate exports so download buttons work without re-running analysis
            html_str = generate_html_report(DataInfo, Data_BPM_summary, output_path=None)

            with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as tmp:
                tmp_path = tmp.name
            con = export_to_duckdb(DataInfo, Data_BPM_summary, db_path=tmp_path)
            con.close()
            with open(tmp_path, "rb") as fh:
                duckdb_bytes = fh.read()
            os.unlink(tmp_path)

            st.session_state.update({
                "DataInfo":     DataInfo,
                "summary":      Data_BPM_summary,
                "html":         html_str,
                "duckdb_bytes": duckdb_bytes,
            })
            st.success(f"Done — {len(Data)} file(s), {len(electrodes)} electrode(s) analysed.")


# ── Display results ───────────────────────────────────────────────────────────
if "summary" in st.session_state:
    DataInfo = st.session_state["DataInfo"]
    summary  = st.session_state["summary"]
    labels   = _file_labels(DataInfo, DataInfo.files_amount)
    elecs    = DataInfo.MEA_electrode_numbers

    # Charts — two columns
    col1, col2 = st.columns(2)
    with col1:
        fig = _line_fig(summary["BPM_avg"], labels, elecs, "BPM Average per File", "BPM")
        st.pyplot(fig)
        plt.close(fig)
    with col2:
        fig = _line_fig(summary["Amplitude_avg"] * 1e6, labels, elecs, "Amplitude Average per File", "Amplitude (µV)")
        st.pyplot(fig)
        plt.close(fig)

    # Normalised charts
    if summary.get("BPM_norm") is not None:
        col3, col4 = st.columns(2)
        with col3:
            fig = _line_fig(summary["BPM_norm"], labels, elecs, "BPM Normalised", "BPM norm")
            st.pyplot(fig)
            plt.close(fig)
        with col4:
            fig = _line_fig(summary["Amplitude_norm"], labels, elecs, "Amplitude Normalised", "Amp norm")
            st.pyplot(fig)
            plt.close(fig)

    # Summary table
    st.subheader("Summary Table")
    st.dataframe(_summary_df(DataInfo, summary), use_container_width=True)

    # Download buttons
    st.subheader("Export")
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            "Download HTML report",
            data=st.session_state["html"].encode("utf-8"),
            file_name="datanalyzer_report.html",
            mime="text/html",
        )
    with dl2:
        st.download_button(
            "Download DuckDB file",
            data=st.session_state["duckdb_bytes"],
            file_name="datanalyzer_results.duckdb",
            mime="application/octet-stream",
        )
