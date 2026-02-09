#!/usr/bin/env python3
"""
Example script: load MEA .h5 data, find peaks, update BPM, create BPM summary.
"""

import argparse

from datanalyzer.part1_raw_data_handling import load_raw_mea_data_to_Data_and_DataInfo
from datanalyzer.part2_peak_handling import find_peaks_in_loop, set_default_filetype_rules_for_peak_finding
from datanalyzer.part3_data_handling_and_analyses import update_Data_BPM, create_BPM_summary


def main():
    p = argparse.ArgumentParser(description="DatAnalyzer: MEA data load, peak find, BPM summary")
    p.add_argument("folder", nargs="?", help="Folder containing .h5 files")
    p.add_argument("--exp-name", default="MEA2020_03_02", help="Experiment name")
    p.add_argument("--meas-name", default="MEA21002b", help="Measurement name")
    p.add_argument("--meas-date", default="2020_03_02", help="Measurement date")
    p.add_argument("--electrodes", type=int, nargs="+", default=None, help="MEA electrode numbers (e.g. 21 28 31 51)")
    p.add_argument("--max-bpm", type=float, default=40, help="Max BPM for peak finding")
    p.add_argument("--min-peak-value", type=float, default=5e-5, help="Min peak amplitude (V)")
    args = p.parse_args()

    if args.folder:
        Data, DataInfo = load_raw_mea_data_to_Data_and_DataInfo(
            exp_name=args.exp_name,
            meas_name=args.meas_name,
            meas_date=args.meas_date,
            file_type=".h5",
            folder_of_files=args.folder,
            file_numbers_to_analyze=None,
            manually_chosen_mea_electrodes=args.electrodes,
        )
    else:
        Data, DataInfo = load_raw_mea_data_to_Data_and_DataInfo(
            exp_name=args.exp_name,
            meas_name=args.meas_name,
            meas_date=args.meas_date,
            folder_of_files=None,
            manually_chosen_mea_electrodes=args.electrodes or [71, 84],
        )
        print("No folder given. Use: python run_mea_analysis.py <path_to_h5_folder> [--electrodes 21 28 31 51]")
        return

    if not Data:
        print("No data loaded.")
        return

    Rule = set_default_filetype_rules_for_peak_finding(
        frame_rate=float(DataInfo.framerate.flat[0]),
    )
    Rule.max_bpm = args.max_bpm
    Rule.min_peak_value = args.min_peak_value
    DataInfo.Rule = Rule

    Data_BPM = find_peaks_in_loop(
        Data,
        DataInfo,
        Rule_in=Rule,
        filenumbers=None,
        datacolumns=None,
        data_multiply=-1,
    )
    Data_BPM = update_Data_BPM(DataInfo, Data_BPM, using_high_peaks=-1)
    Data_BPM_summary = create_BPM_summary(DataInfo, Data_BPM)

    print("Done.")
    print("  Data: %d files" % len(Data))
    print("  Data_BPM_summary.BPM_avg shape:", Data_BPM_summary["BPM_avg"].shape)
    print("  Data_BPM_summary.Amplitude_avg shape:", Data_BPM_summary["Amplitude_avg"].shape)


if __name__ == "__main__":
    main()
