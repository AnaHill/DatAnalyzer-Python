"""
Create Data_BPM_summary from Data_BPM and DataInfo.
"""

from typing import List, Optional, Any
import numpy as np


def create_BPM_summary(
    DataInfo: Any,
    Data_BPM: List[dict],
    normalizing_indexes: Optional[List[int]] = None,
    chosen_datacol_indexes: Optional[List[int]] = None,
) -> dict:
    """
    Build summary: Amount_of_peaks, BPM_avg, BPM_avg_stdpros, peak_values, peak_locations,
    Amplitude_avg, Amplitude_std_pros, peak_width_avg, normalizing, peak_distances.
    """
    n_files = DataInfo.files_amount
    if chosen_datacol_indexes is None:
        chosen_datacol_indexes = list(range(1, len(DataInfo.datacol_numbers) + 1))
    ind_col = chosen_datacol_indexes
    n_cols = len(DataInfo.datacol_numbers)

    if normalizing_indexes is None:
        try:
            start_sec = DataInfo.hypoxia["start_time_sec"]
            idx_before = np.where(DataInfo.measurement_time["time_sec"] <= start_sec)[0]
            if len(idx_before) >= 3:
                normalizing_indexes = [idx_before[-3], idx_before[-2], idx_before[-1]]
            elif len(idx_before) == 2:
                normalizing_indexes = [idx_before[-2], idx_before[-1]]
            else:
                normalizing_indexes = [0]
        except (AttributeError, KeyError, TypeError):
            normalizing_indexes = [0]

    out = {}
    out["Amount_of_peaks"] = np.full((n_files, n_cols), np.nan)
    out["BPM_avg"] = np.full((n_files, n_cols), np.nan)
    out["BPM_avg_stdpros"] = np.full((n_files, n_cols), np.nan)
    out["peak_values"] = {kk: Data_BPM[kk].get("peak_values", {}) for kk in range(n_files)}
    out["peak_locations"] = {kk: Data_BPM[kk].get("peak_locations", {}) for kk in range(n_files)}
    out["peak_widths"] = {kk: Data_BPM[kk].get("peak_widths", {}) for kk in range(n_files)}
    out["Amplitude_avg"] = np.full((n_files, len(ind_col)), np.nan)
    out["Amplitude_std_pros"] = np.full((n_files, len(ind_col)), np.nan)
    out["peak_width_avg"] = np.full((n_files, len(ind_col)), np.nan)
    out["peak_width_std_pros"] = np.full((n_files, len(ind_col)), np.nan)
    out["normalizing_indexes"] = normalizing_indexes
    out["peak_distances"] = {}
    out["peak_distances_avg"] = np.full((n_files, n_cols), np.nan)
    out["peak_distances_std"] = np.full((n_files, n_cols), np.nan)

    for kk in range(n_files):
        d = Data_BPM[kk]
        if "Amount_of_peaks" not in d:
            continue
        out["Amount_of_peaks"][kk, :] = d["Amount_of_peaks"]
        out["BPM_avg"][kk, :] = d["BPM_avg"]
        dt = d.get("peak_avg_distance_in_ms", np.full((n_cols, 2), np.nan))
        if dt.shape[0] >= n_cols:
            stdp = np.where(dt[:, 0] > 0, dt[:, 1] / dt[:, 0] * 100, np.nan)
            out["BPM_avg_stdpros"][kk, :] = stdp

    for kk in range(n_files):
        for ii, ind in enumerate(ind_col):
            pv = out["peak_values"].get(kk, {}).get(ind, np.array([np.nan]))
            pv = np.atleast_1d(pv)
            out["Amplitude_avg"][kk, ii] = np.nanmean(pv)
            if np.nanmean(pv) != 0:
                out["Amplitude_std_pros"][kk, ii] = np.nanstd(pv) / np.nanmean(pv) * 100
            pw = out["peak_widths"].get(kk, {}).get(ind, np.array([np.nan]))
            pw = np.atleast_1d(pw)
            out["peak_width_avg"][kk, ii] = np.nanmean(pw)
            if np.nanmean(pw) != 0:
                out["peak_width_std_pros"][kk, ii] = np.nanstd(pw) / np.nanmean(pw) * 100

    norm_idx = np.array(normalizing_indexes)
    norm_idx = norm_idx[norm_idx < n_files]
    if norm_idx.size > 0:
        out["Amplitude_norm"] = out["Amplitude_avg"] / np.nanmean(out["Amplitude_avg"][norm_idx, :], axis=0)
        out["BPM_norm"] = out["BPM_avg"] / np.nanmean(out["BPM_avg"][norm_idx, :], axis=0)
    else:
        out["Amplitude_norm"] = out["Amplitude_avg"] / (np.nanmean(out["Amplitude_avg"], axis=0) + 1e-12)
        out["BPM_norm"] = out["BPM_avg"] / (np.nanmean(out["BPM_avg"], axis=0) + 1e-12)

    for file_index in range(n_files):
        try:
            fs = float(DataInfo.framerate[file_index, 0])
        except (IndexError, TypeError):
            fs = float(DataInfo.framerate.flat[0])
        out["peak_distances"][file_index] = {}
        for kk, col_index in enumerate(chosen_datacol_indexes):
            try:
                locs = Data_BPM[file_index]["peak_locations"].get(col_index, np.array([]))
                locs = np.atleast_1d(locs)
                if locs.size < 2:
                    out["peak_distances"][file_index][col_index] = np.array([np.nan])
                else:
                    out["peak_distances"][file_index][col_index] = np.diff(locs) / fs * 1e3
            except Exception:
                out["peak_distances"][file_index][col_index] = np.array([np.nan])
            arr = out["peak_distances"][file_index][col_index]
            arr = np.atleast_1d(arr)
            arr = arr[~np.isnan(arr)]
            if arr.size > 0:
                out["peak_distances_avg"][file_index, col_index - 1] = np.mean(arr)
                out["peak_distances_std"][file_index, col_index - 1] = np.std(arr)
            else:
                out["peak_distances_avg"][file_index, col_index - 1] = np.nan
                out["peak_distances_std"][file_index, col_index - 1] = np.nan

    return out
