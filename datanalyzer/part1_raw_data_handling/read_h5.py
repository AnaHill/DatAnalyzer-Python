"""
Read MEA data from HDF5 (.h5) files (Multichannel Systems format).
"""

from typing import Optional, Tuple
import numpy as np
import h5py


def read_raw_mea_file(
    info: "object",
    index: int,
) -> Tuple[dict, float]:
    """
    Read single MEA .h5 file: duration, ChannelData, InfoChannel, framerate.
    index is 1-based file index. Returns (rawmeadata dict, framerate).
    """
    path = info.folder_raw_files + info.file_names[index - 1]
    rawmeadata = {}
    with h5py.File(path, "r") as f:
        try:
            dur_attr = f["/Data/Recording_0"].attrs.get("Duration")
            rawmeadata["duration"] = float(dur_attr) * 1e-6
        except (KeyError, TypeError):
            rawmeadata["duration"] = 60.0
        ds = f["/Data/Recording_0/AnalogStream/Stream_0/ChannelData"]
        rawmeadata["MCSFile"] = np.array(ds[:])
        rawmeadata["info"] = {}
        info_ds = f["/Data/Recording_0/AnalogStream/Stream_0/InfoChannel"]
        for key in info_ds.keys():
            rawmeadata["info"][key] = np.array(info_ds[key][:])
        n_rows = rawmeadata["MCSFile"].shape[0]
        rawmeadata["framerate"] = n_rows / rawmeadata["duration"]
    return rawmeadata, rawmeadata["framerate"]


def read_chosen_mea_electrode_data(info: "object", rawmeadata: dict) -> np.ndarray:
    """
    From raw MEA file data, extract chosen electrode columns and convert to Volts.
    Columns are 1-based in MEA_columns; HDF5 indexing uses 0-based so we use col - 1.
    """
    cols = np.asarray(info.MEA_columns, dtype=int) - 1
    MCS = rawmeadata["MCSFile"]
    inf = rawmeadata["info"]
    ADZero = inf["ADZero"][cols]
    ConversionFactor = inf["ConversionFactor"][cols]
    Exponent = inf["Exponent"][cols]
    data = (MCS[:, cols].astype(np.float64) - ADZero) * (
        ConversionFactor.astype(np.float64) * (10.0 ** Exponent.astype(np.float64))
    )
    return data


def read_h5_to_data(
    info: "object",
    index: int,
    how_many_datarows: int = 0,
    how_many_datacolumns: Optional[int] = None,
    start_indexes: Optional[Tuple[int, int]] = None,
) -> Tuple[np.ndarray, dict, float]:
    """
    Read single .h5 file into converted data array.
    index: 1-based file index.
    Returns (data 2D array, h5info dict, framerate).
    """
    if start_indexes is None:
        start_indexes = (1, 1)
    if how_many_datacolumns is None:
        how_many_datacolumns = len(info.datacol_numbers) if getattr(info, "datacol_numbers", None) else len(info.MEA_columns)
    path = info.folder_raw_files + info.file_names[index - 1]
    start_row, start_col = start_indexes
    start_row -= 1
    start_col -= 1
    h5info = {}
    with h5py.File(path, "r") as f:
        info_ch = f["/Data/Recording_0/AnalogStream/Stream_0/InfoChannel"]
        for key in info_ch.keys():
            h5info[key] = np.array(info_ch[key][:])
        try:
            h5info["duration"] = float(f["/Data/Recording_0"].attrs["Duration"]) * 1e-6
        except (KeyError, TypeError):
            h5info["duration"] = 60.0
        ts = f["/Data/Recording_0/AnalogStream/Stream_0/ChannelDataTimeStamps"][:]
        if ts.size >= 2:
            index_length = int(ts[-1] - ts[-2] + 1)
        else:
            index_length = 1
        h5info["framerate"] = index_length / h5info["duration"]
        ds = f["/Data/Recording_0/AnalogStream/Stream_0/ChannelData"]
        n_cols_total = ds.shape[1]
        n_read_cols = min(how_many_datacolumns, n_cols_total - start_col)
        if how_many_datarows == 0:
            MCS = ds[start_row:, start_col : start_col + n_read_cols]
        else:
            MCS = ds[start_row : start_row + how_many_datarows, start_col : start_col + n_read_cols]
        MCS = np.array(MCS)
    cols_idx = np.arange(start_col, start_col + MCS.shape[1])
    ADZero = h5info["ADZero"][cols_idx]
    ConversionFactor = h5info["ConversionFactor"][cols_idx]
    Exponent = h5info["Exponent"][cols_idx]
    data = (MCS.astype(np.float64) - ADZero) * (
        ConversionFactor.astype(np.float64) * (10.0 ** Exponent.astype(np.float64))
    )
    return data, h5info, h5info["framerate"]
