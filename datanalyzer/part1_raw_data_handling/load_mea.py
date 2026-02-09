"""
Load raw MEA data from .h5 folder into Data (list of dicts) and DataInfo.
"""

from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np

from datanalyzer.models import DataInfo, Rule
from .mea_layout import read_mea_electrode_layout, find_mea_electrode_index, read_wanted_electrodes_of_measurement
from .datetime_utils import convert_end_string_in_filename_to_datetime
from .read_h5 import read_raw_mea_file, read_chosen_mea_electrode_data


def list_files(
    file_type: str = ".h5",
    folder_to_start: Optional[str] = None,
) -> Tuple[str, List[str]]:
    """List .h5 files in folder. Returns (folder path, list of filenames)."""
    if folder_to_start is None:
        raise ValueError("folder_to_start must be provided (path to folder containing .h5 files)")
    folder = Path(folder_to_start)
    if not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")
    files = sorted(f.name for f in folder.glob(f"*{file_type}"))
    return str(folder) + ("/" if not str(folder).endswith("/") else ""), files


def create_DataInfo_start(
    folder_raw_files: str,
    file_names: List[str],
    exp_name: str = "",
    meas_name: str = "",
    meas_date: str = "",
    file_type: str = ".h5",
) -> DataInfo:
    """Create initial DataInfo from folder and file list."""
    info = DataInfo(
        experiment_name=exp_name,
        measurement_name=meas_name,
        measurement_date=meas_date,
        folder_raw_files=folder_raw_files,
        file_names=file_names,
        files_amount=len(file_names),
        file_type=file_type,
    )
    info.datacol_numbers = []
    return info


def load_raw_mea_data_to_Data_and_DataInfo(
    exp_name: Optional[str] = None,
    meas_name: Optional[str] = None,
    meas_date: Optional[str] = None,
    file_type: str = ".h5",
    mea_layout_name: Optional[str] = None,
    folder_of_files: Optional[str] = None,
    file_numbers_to_analyze: Optional[List[int]] = None,
    manually_chosen_mea_electrodes: Optional[List[int]] = None,
) -> Tuple[List[dict], DataInfo]:
    """
    Load MEA .h5 data into Data and DataInfo.
    If folder_of_files is None, only DataInfo is set up (no loading).
    file_numbers_to_analyze: 1-based indices into file list (default: all).
    manually_chosen_mea_electrodes: electrode numbers to load; if None, uses
    read_wanted_electrodes_of_measurement(exp_name, meas_name) or all from layout.
    """
    exp_name = exp_name or "Exp_11311_EURCCS_p32_180820"
    meas_name = meas_name or "mea21001a"
    meas_date = meas_date or "2020_09_15"
    file_type = file_type or ".h5"
    mea_layout_name = mea_layout_name or "MEA_64_electrode_layout.txt"

    electrode_layout = read_mea_electrode_layout(mea_layout_name=mea_layout_name)

    if manually_chosen_mea_electrodes is not None and len(manually_chosen_mea_electrodes) > 0:
        mea_electrode_numbers = list(manually_chosen_mea_electrodes)
    else:
        mea_electrode_numbers = read_wanted_electrodes_of_measurement(
            exp_name, meas_name, electrode_layout
        )
    if not mea_electrode_numbers and electrode_layout is not None:
        mea_electrode_numbers = electrode_layout.iloc[:, 0].tolist()

    mea_columns = find_mea_electrode_index(mea_electrode_numbers, electrode_layout)
    mea_columns = mea_columns.tolist()

    if folder_of_files is None:
        info = DataInfo(
            experiment_name=exp_name,
            measurement_name=meas_name,
            measurement_date=meas_date,
            folder_raw_files="",
            file_names=[],
            files_amount=0,
            file_type=file_type,
            electrode_layout=electrode_layout,
            MEA_electrode_numbers=mea_electrode_numbers,
            MEA_columns=mea_columns,
            datacol_numbers=list(range(1, len(mea_columns) + 1)),
        )
        info.Rule = Rule(frame_rate=25e3, signal="MEA", max_bpm=120, min_peak_value=2.5e-5)
        return [], info

    folder_raw_files, filename_list = list_files(file_type, folder_of_files)
    if file_numbers_to_analyze is None:
        file_numbers_to_analyze = list(range(1, len(filename_list) + 1))
    file_names = [filename_list[i - 1] for i in file_numbers_to_analyze]

    info = create_DataInfo_start(
        folder_raw_files, file_names, exp_name, meas_name, meas_date, file_type
    )
    info.electrode_layout = electrode_layout
    info.MEA_electrode_numbers = mea_electrode_numbers
    info.MEA_columns = mea_columns
    info.datacol_numbers = list(range(1, len(mea_columns) + 1))
    info.Rule = Rule(frame_rate=25e3, signal="MEA", max_bpm=120, min_peak_value=2.5e-5)

    n_files = len(file_names)
    framerates = []
    measurement_datetime = []
    measurement_duration = []
    measurement_time_sec = []
    measurement_names = []
    Data = []

    for idx in range(1, n_files + 1):
        try:
            dt = convert_end_string_in_filename_to_datetime(info.file_names[idx - 1])
        except Exception:
            import datetime as dtmod
            dt = dtmod.datetime.now()
        rawmeadata, fs = read_raw_mea_file(info, idx)
        chosen = read_chosen_mea_electrode_data(info, rawmeadata)

        framerates.append(fs)
        measurement_datetime.append(dt)
        if idx == 1:
            meas_duration_sec = 0.0
        else:
            meas_duration_sec = (dt - measurement_datetime[0]).total_seconds()
        measurement_duration.append(meas_duration_sec)
        measurement_time_sec.append(meas_duration_sec)
        measurement_names.append(info.file_names[idx - 1].replace(".h5", ""))

        Data.append({
            "data": chosen,
            "file_index": idx,
        })

    info.framerate = np.array(framerates).reshape(-1, 1)
    info.measurement_time["datetime"] = np.array(measurement_datetime)
    info.measurement_time["duration"] = np.array(measurement_duration, dtype=float)
    info.measurement_time["time_sec"] = np.array(measurement_time_sec, dtype=float)
    info.measurement_time["names"] = measurement_names

    return Data, info
