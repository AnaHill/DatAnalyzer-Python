"""Export MEA analysis results to DuckDB tables."""

import duckdb
import numpy as np
from typing import Any, Optional


def export_to_duckdb(
    DataInfo: Any,
    Data_BPM_summary: dict,
    db_path: str = ":memory:",
    con: Optional[duckdb.DuckDBPyConnection] = None,
) -> duckdb.DuckDBPyConnection:
    """
    Store DataInfo metadata and Data_BPM_summary into DuckDB tables.

    Tables:
      experiments  — one row per call (experiment/measurement metadata)
      files        — one row per .h5 file
      bpm_summary  — one row per (file × electrode): BPM, amplitude, peak stats
      peak_distances — one row per inter-peak interval (ms)

    Returns the DuckDB connection so the caller can query or persist it.
    Use db_path=':memory:' for in-process analysis; pass a file path to persist.
    """
    if con is None:
        con = duckdb.connect(db_path)

    _create_schema(con)
    _insert_experiment(con, DataInfo)
    _insert_files(con, DataInfo)
    _insert_bpm_summary(con, DataInfo, Data_BPM_summary)
    _insert_peak_distances(con, DataInfo, Data_BPM_summary)

    return con


def _create_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            exp_name    VARCHAR,
            meas_name   VARCHAR,
            meas_date   VARCHAR,
            framerate   DOUBLE
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS files (
            file_index  INTEGER,
            file_name   VARCHAR,
            start_time  VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS bpm_summary (
            file_index       INTEGER,
            electrode_number INTEGER,
            amount_of_peaks  INTEGER,
            bpm_avg          DOUBLE,
            bpm_avg_stdpros  DOUBLE,
            amplitude_avg    DOUBLE,
            amplitude_std_pros DOUBLE,
            peak_width_avg   DOUBLE,
            peak_width_std_pros DOUBLE,
            bpm_norm         DOUBLE,
            amplitude_norm   DOUBLE
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS peak_distances (
            file_index       INTEGER,
            electrode_number INTEGER,
            peak_index       INTEGER,
            distance_ms      DOUBLE
        )
    """)


def _insert_experiment(con: duckdb.DuckDBPyConnection, DataInfo: Any) -> None:
    fs = float(DataInfo.framerate.flat[0]) if DataInfo.framerate.size > 0 else 0.0
    con.execute(
        "INSERT INTO experiments VALUES (?, ?, ?, ?)",
        [DataInfo.experiment_name, DataInfo.measurement_name, DataInfo.measurement_date, fs],
    )


def _insert_files(con: duckdb.DuckDBPyConnection, DataInfo: Any) -> None:
    datetimes = DataInfo.measurement_time.get("datetime", [])
    for i, fname in enumerate(DataInfo.file_names):
        start = str(datetimes[i]) if i < len(datetimes) else ""
        con.execute("INSERT INTO files VALUES (?, ?, ?)", [i, fname, start])


def _nan_to_none(v: float) -> Optional[float]:
    if isinstance(v, float) and np.isnan(v):
        return None
    return v


def _insert_bpm_summary(
    con: duckdb.DuckDBPyConnection, DataInfo: Any, summary: dict
) -> None:
    n_files, n_cols = summary["BPM_avg"].shape
    electrodes = DataInfo.MEA_electrode_numbers

    for fi in range(n_files):
        for ci in range(n_cols):
            elec = int(electrodes[ci]) if ci < len(electrodes) else ci + 1

            raw_count = summary["Amount_of_peaks"][fi, ci]
            amt = None if (isinstance(raw_count, float) and np.isnan(raw_count)) else int(raw_count)

            def _f(key: str) -> Optional[float]:
                return _nan_to_none(float(summary[key][fi, ci]))

            con.execute(
                "INSERT INTO bpm_summary VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    fi, elec, amt,
                    _f("BPM_avg"), _f("BPM_avg_stdpros"),
                    _f("Amplitude_avg"), _f("Amplitude_std_pros"),
                    _f("peak_width_avg"), _f("peak_width_std_pros"),
                    _f("BPM_norm"), _f("Amplitude_norm"),
                ],
            )


def _insert_peak_distances(
    con: duckdb.DuckDBPyConnection, DataInfo: Any, summary: dict
) -> None:
    electrodes = DataInfo.MEA_electrode_numbers
    n_cols = len(DataInfo.datacol_numbers)
    col_range = list(range(1, n_cols + 1))

    for fi, file_dists in summary.get("peak_distances", {}).items():
        for ci, col_idx in enumerate(col_range):
            elec = int(electrodes[ci]) if ci < len(electrodes) else ci + 1
            dists = np.atleast_1d(file_dists.get(col_idx, np.array([])))
            for pi, d in enumerate(dists):
                if not np.isnan(d):
                    con.execute(
                        "INSERT INTO peak_distances VALUES (?, ?, ?, ?)",
                        [int(fi), elec, pi, float(d)],
                    )
