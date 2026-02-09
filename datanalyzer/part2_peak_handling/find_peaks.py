"""
Find peaks in MEA data (low or high) using scipy.signal.find_peaks.
"""

from typing import List, Optional, Any
import numpy as np
from scipy.signal import find_peaks as scipy_find_peaks

from datanalyzer.models import Rule
from .rules import set_default_filetype_rules_for_peak_finding


def find_peaks_in_loop(
    Data: List[dict],
    DataInfo: Any,
    Rule_in: Optional[Rule] = None,
    filenumbers: Optional[List[int]] = None,
    datacolumns: Optional[List[int]] = None,
    data_multiply: int = -1,
    Data_BPM: Optional[List[dict]] = None,
) -> List[dict]:
    """
    Find peaks in Data (list of {data, file_index}) for each file and datacolumn.
    data_multiply: 1 = high peaks, -1 = low peaks (invert signal).
    Returns Data_BPM: list of dicts per file with peak_values_low/high,
    peak_locations_low/high, peak_widths_low/high, Amount_of_peaks_low/high.
    """
    if Rule_in is None:
        if getattr(DataInfo, "Rule", None) is not None:
            Rule_in = DataInfo.Rule
        else:
            Rule_in = set_default_filetype_rules_for_peak_finding(
                frame_rate=float(DataInfo.framerate.flat[0]) if DataInfo.framerate.size else 25e3,
            )
            DataInfo.Rule = Rule_in

    n_files = len(Data)
    if filenumbers is None:
        filenumbers = list(range(1, n_files + 1))
    if datacolumns is None:
        datacolumns = list(range(1, Data[0]["data"].shape[1] + 1))

    min_peak_distance = Rule_in.frame_rate * 60.0 / Rule_in.max_bpm
    min_peak_value = getattr(Rule_in, "MinPeakValue", Rule_in.min_peak_value)
    min_peak_width = getattr(Rule_in, "minimum_peak_width", 50)

    n_cols_data = Data[0]["data"].shape[1]
    if Data_BPM is None:
        Data_BPM = [{} for _ in range(n_files)]
    while len(Data_BPM) < n_files:
        Data_BPM.append({})

    for kk in range(n_files):
        Data_BPM[kk].setdefault("file_index", kk + 1)
        Data_BPM[kk].setdefault("peak_values_high", {})
        Data_BPM[kk].setdefault("peak_locations_high", {})
        Data_BPM[kk].setdefault("peak_widths_high", {})
        Data_BPM[kk].setdefault("Amount_of_peaks_high", np.zeros(n_cols_data))
        Data_BPM[kk].setdefault("peak_values_low", {})
        Data_BPM[kk].setdefault("peak_locations_low", {})
        Data_BPM[kk].setdefault("peak_widths_low", {})
        Data_BPM[kk].setdefault("Amount_of_peaks_low", np.zeros(n_cols_data))

    for pp, file_idx in enumerate(filenumbers):
        if file_idx < 1 or file_idx > n_files:
            continue
        ii = file_idx - 1
        raw_data = Data[ii]["data"] * data_multiply
        n_cols = raw_data.shape[1]
        for col in datacolumns:
            if col < 1 or col > n_cols:
                continue
            data_to_check = raw_data[:, col - 1].copy()
            data_to_check[data_to_check < 0] = 0
            locs, props = scipy_find_peaks(
                data_to_check,
                height=min_peak_value,
                distance=int(min_peak_distance),
                width=min_peak_width,
            )
            pks = data_to_check[locs]
            w = props.get("widths", np.full(len(locs), np.nan))
            if not np.iterable(w):
                w = np.full(len(locs), w)
            locs_1based = locs + 1

            if data_multiply > 0:
                Data_BPM[ii]["peak_values_high"][col] = pks
                Data_BPM[ii]["peak_locations_high"][col] = locs_1based
                Data_BPM[ii]["peak_widths_high"][col] = w
                Data_BPM[ii]["Amount_of_peaks_high"][col - 1] = len(pks)
            else:
                Data_BPM[ii]["peak_values_low"][col] = pks * data_multiply
                Data_BPM[ii]["peak_locations_low"][col] = locs_1based
                Data_BPM[ii]["peak_widths_low"][col] = w
                Data_BPM[ii]["Amount_of_peaks_low"][col - 1] = len(pks)

    return Data_BPM
