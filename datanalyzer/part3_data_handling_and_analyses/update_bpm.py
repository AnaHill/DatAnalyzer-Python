"""
Update Data_BPM with peak distances (ms), BPM_avg, and set active peak set (low/high).
"""

from typing import List, Any
import numpy as np


def update_Data_BPM_peaks_with_low_or_high_peaks(
    file_index: int,
    datacolumn_index: int,
    low_or_high_peaks: str,
    Data_BPM: List[dict],
) -> List[dict]:
    """Set active peak set for (file_index, datacolumn_index) to low or high."""
    kk = file_index - 1
    pp = datacolumn_index
    if kk < 0 or kk >= len(Data_BPM):
        return Data_BPM
    d = Data_BPM[kk]
    if low_or_high_peaks == "low":
        d["peak_locations"] = d.get("peak_locations", {})
        d["peak_values"] = d.get("peak_values", {})
        d["peak_locations"][pp] = d["peak_locations_low"].get(pp, np.array([]))
        d["peak_values"][pp] = d["peak_values_low"].get(pp, np.array([]))
        d.setdefault("Amount_of_peaks", np.zeros_like(d["Amount_of_peaks_low"]))
        d["Amount_of_peaks"][pp - 1] = d["Amount_of_peaks_low"][pp - 1]
        d.setdefault("BPM_avg", np.zeros_like(d["Amount_of_peaks_low"], dtype=float))
        d["BPM_avg"][pp - 1] = d["BPM_avg_low"][pp - 1]
        d.setdefault("peak_avg_distance_in_ms", np.zeros((len(d["Amount_of_peaks_low"]), 2)))
        d["peak_avg_distance_in_ms"][pp - 1, :] = d["peak_avg_distance_in_ms_low"][pp - 1, :]
        d.setdefault("peak_distances_in_ms", {})
        d["peak_distances_in_ms"][pp] = d["peak_distances_in_ms_low"].get(pp, np.array([]))
        d.setdefault("peak_widths", {})
        d["peak_widths"][pp] = d["peak_widths_low"].get(pp, np.array([]))
    else:
        d["peak_locations"] = d.get("peak_locations", {})
        d["peak_values"] = d.get("peak_values", {})
        d["peak_locations"][pp] = d["peak_locations_high"].get(pp, np.array([]))
        d["peak_values"][pp] = d["peak_values_high"].get(pp, np.array([]))
        d.setdefault("Amount_of_peaks", np.zeros_like(d["Amount_of_peaks_high"]))
        d["Amount_of_peaks"][pp - 1] = d["Amount_of_peaks_high"][pp - 1]
        d.setdefault("BPM_avg", np.zeros_like(d["Amount_of_peaks_high"], dtype=float))
        d["BPM_avg"][pp - 1] = d["BPM_avg_high"][pp - 1]
        d.setdefault("peak_avg_distance_in_ms", np.zeros((len(d["Amount_of_peaks_high"]), 2)))
        d["peak_avg_distance_in_ms"][pp - 1, :] = d["peak_avg_distance_in_ms_high"][pp - 1, :]
        d.setdefault("peak_distances_in_ms", {})
        d["peak_distances_in_ms"][pp] = d["peak_distances_in_ms_high"].get(pp, np.array([]))
        d.setdefault("peak_widths", {})
        d["peak_widths"][pp] = d["peak_widths_high"].get(pp, np.array([]))
    return Data_BPM


def should_high_peak_data_be_used(
    data: dict,
    elcol: int,
    high_peaks_ratio_to_low_peaks: float = 0.8,
) -> int:
    """Return 1 if high peaks should be used for this file/column, else 0."""
    n_high = int(data["Amount_of_peaks_high"][elcol - 1])
    n_low = int(data["Amount_of_peaks_low"][elcol - 1])
    if n_high <= high_peaks_ratio_to_low_peaks * n_low:
        return 0
    try:
        pvh = data["peak_values_high"][elcol]
        pvl = np.abs(data["peak_values_low"][elcol])
        dh = data["peak_avg_distance_in_ms_high"][elcol - 1, :]
        dl = data["peak_avg_distance_in_ms_low"][elcol - 1, :]
    except (KeyError, IndexError):
        return 0
    if len(pvh) == 0 or len(pvl) == 0:
        return 1 if (n_low < 3 and n_high > 2) or (n_low < 2 and n_high > 1) else 0
    pvh_std_per = np.nanstd(pvh) / np.nanmean(pvh) * 100
    pvl_std_per = np.nanstd(pvl) / np.nanmean(pvl) * 100
    bpm_std_h = dh[1] / dh[0] * 100 if dh[0] else 0
    bpm_std_l = dl[1] / dl[0] * 100 if dl[0] else 0
    use_high = 0
    if np.nanmean(pvh) > np.nanmean(pvl):
        if pvh_std_per < pvl_std_per:
            use_high = 1
        elif bpm_std_h < bpm_std_l:
            use_high = 1
        elif (np.nanmean(pvh) / np.nanmean(pvl)) > (pvh_std_per / pvl_std_per if pvl_std_per else 1):
            use_high = 1
        elif (np.nanmean(pvh) / np.nanmean(pvl)) > (bpm_std_h / bpm_std_l if bpm_std_l else 1):
            use_high = 1
    if bpm_std_l / (bpm_std_h or 1) > 1.2:
        use_high = 1
    if n_low < 3 and n_high > 2:
        use_high = 1
    if n_low < 2 and n_high > 1:
        use_high = 1
    return use_high


def update_Data_BPM(
    DataInfo: Any,
    Data_BPM: List[dict],
    using_high_peaks: int = -1,
) -> List[dict]:
    """
    Compute peak distances (ms), BPM_avg, peak_avg_distance_in_ms for each file/column,
    then set active peak set (low or high) per column.
    using_high_peaks: -1 = auto (should_high_peak_data_be_used), 0 = always low, 1 = always high.
    """
    n_files = len(Data_BPM)
    try:
        n_cols = len(DataInfo.datacol_numbers)
    except (AttributeError, TypeError):
        n_cols = Data_BPM[0]["Amount_of_peaks_low"].shape[0]

    for kk in range(n_files):
        Data_BPM[kk]["file_index"] = kk + 1
        try:
            fs = float(DataInfo.framerate[kk, 0])
        except (IndexError, TypeError):
            fs = float(DataInfo.framerate.flat[0])
        for pp in range(1, n_cols + 1):
            for suffix in ("low", "high"):
                locs_key = f"peak_locations_{suffix}"
                dist_key = f"peak_distances_in_ms_{suffix}"
                avg_dist_key = f"peak_avg_distance_in_ms_{suffix}"
                bpm_key = f"BPM_avg_{suffix}"
                amount_key = f"Amount_of_peaks_{suffix}"
                try:
                    pks = Data_BPM[kk][locs_key].get(pp, np.array([]))
                except (TypeError, KeyError):
                    pks = np.array([])
                if not isinstance(pks, np.ndarray):
                    pks = np.atleast_1d(pks)
                if pks.size == 0:
                    Data_BPM[kk].setdefault(dist_key, {})
                    Data_BPM[kk][dist_key][pp] = np.array([])
                    if avg_dist_key not in Data_BPM[kk]:
                        Data_BPM[kk][avg_dist_key] = np.full((n_cols, 2), np.nan)
                    if bpm_key not in Data_BPM[kk]:
                        Data_BPM[kk][bpm_key] = np.full(n_cols, np.nan)
                    continue
                peak_times = (pks - 1) / fs
                dist_ms = np.diff(peak_times) * 1e3
                Data_BPM[kk].setdefault(dist_key, {})
                Data_BPM[kk][dist_key][pp] = dist_ms
                if dist_ms.size > 0:
                    dist_avg_ms = np.array([np.mean(dist_ms), np.std(dist_ms)])
                    BPM_avg = 60.0 / (dist_avg_ms[0] / 1000.0)
                else:
                    dist_avg_ms = np.array([np.nan, np.nan])
                    BPM_avg = np.nan
                Data_BPM[kk].setdefault(avg_dist_key, np.full((n_cols, 2), np.nan))
                Data_BPM[kk][avg_dist_key][pp - 1, :] = dist_avg_ms
                Data_BPM[kk].setdefault(bpm_key, np.full(n_cols, np.nan))
                Data_BPM[kk][bpm_key][pp - 1] = BPM_avg
                Data_BPM[kk][amount_key][pp - 1] = len(pks)

            use_high = using_high_peaks
            if using_high_peaks < 0:
                use_high = should_high_peak_data_be_used(Data_BPM[kk], pp)
            update_Data_BPM_peaks_with_low_or_high_peaks(
                kk + 1, pp, "high" if use_high else "low", Data_BPM
            )
    return Data_BPM
