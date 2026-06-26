#!/usr/bin/env python3
"""
Generate synthetic MEA HDF5 test files compatible with DatAnalyzer.

Produces N files in a target folder.  Each file contains realistic-looking
MEA field potential signals: Gaussian background noise + periodic negative
spikes on electrodes 71 and 84 (the default electrodes in run_mea_analysis.py).

Usage:
    python create_test_data.py                     # writes 5 files to test_data/
    python create_test_data.py my_folder --n 8 --bpm 35

Then run analysis:
    python run_mea_analysis.py test_data --electrodes 71 84 --max-bpm 40 --report report.html
"""

import argparse
import os
import numpy as np
import h5py

# ── recording parameters ──────────────────────────────────────────────────────
N_ELECTRODES = 60       # columns in the HDF5 (matches 64-electrode MEA layout)
FRAME_RATE   = 25_000   # Hz
DURATION_S   = 10.0     # seconds per file
NOISE_UV     = 5.0      # µV RMS background noise
SPIKE_AMP_UV = 50.0     # µV peak amplitude

# Electrode 71 → layout column 37 → 0-based index 36
# Electrode 84 → layout column 45 → 0-based index 44
SIGNAL_COLS = {36: "E71", 44: "E84"}


def _spike_template(amp_uv: float, half_width: int = 80) -> np.ndarray:
    t = np.arange(-half_width, half_width)
    return -amp_uv * np.exp(-0.5 * (t / (half_width / 3.0)) ** 2)


def _make_signal(n_samples: int, bpm: float, amp_uv: float, noise_uv: float, rng: np.random.Generator) -> np.ndarray:
    sig = rng.normal(0.0, noise_uv, n_samples)
    interval = int(60.0 / bpm * FRAME_RATE)
    template = _spike_template(amp_uv)
    hw = len(template) // 2
    for center in range(hw, n_samples - hw, interval):
        sig[center - hw : center + hw] += template
    return sig


def _write_h5(path: str, bpm_e71: float, bpm_e84: float, file_idx: int) -> None:
    n_samples = int(FRAME_RATE * DURATION_S)
    duration_us = int(DURATION_S * 1e6)

    rng = np.random.default_rng(seed=file_idx)

    # All electrodes: noise only
    data_uv = rng.normal(0.0, NOISE_UV, (n_samples, N_ELECTRODES))

    # Inject spikes on the two active electrodes
    data_uv[:, 36] = _make_signal(n_samples, bpm_e71, SPIKE_AMP_UV, NOISE_UV, rng)
    data_uv[:, 44] = _make_signal(n_samples, bpm_e84, SPIKE_AMP_UV * 0.9, NOISE_UV, rng)

    # Calibration: 1 ADC count = 1 µV  →  ConversionFactor=1, Exponent=-6
    data_adc = np.round(data_uv).astype(np.int32)

    with h5py.File(path, "w") as f:
        rec = f.create_group("Data/Recording_0")
        rec.attrs["Duration"] = duration_us

        stream = rec.create_group("AnalogStream/Stream_0")
        stream.create_dataset("ChannelData", data=data_adc, compression="gzip", compression_opts=4)
        # Two-entry timestamp so framerate = (ts[1]-ts[0]+1) / duration
        stream.create_dataset("ChannelDataTimeStamps", data=np.array([0, n_samples - 1]))

        info = stream.create_group("InfoChannel")
        info.create_dataset("ADZero",            data=np.zeros(N_ELECTRODES, dtype=np.int32))
        info.create_dataset("ConversionFactor",  data=np.ones(N_ELECTRODES,  dtype=np.float64))
        info.create_dataset("Exponent",          data=np.full(N_ELECTRODES, -6, dtype=np.int32))


def main():
    p = argparse.ArgumentParser(description="Generate synthetic MEA .h5 test files")
    p.add_argument("folder", nargs="?", default="test_data",
                   help="Output folder (default: test_data/)")
    p.add_argument("--n", type=int, default=5, dest="n_files",
                   help="Number of files (default: 5)")
    p.add_argument("--bpm", type=float, default=30.0,
                   help="Centre BPM for electrode 71 (default: 30)")
    args = p.parse_args()

    os.makedirs(args.folder, exist_ok=True)

    # Spread BPM ±20%% across files to simulate a time-series experiment
    bpms = np.linspace(args.bpm * 0.8, args.bpm * 1.2, args.n_files)

    print(f"Generating {args.n_files} synthetic MEA file(s) in '{args.folder}/'")
    for i, bpm in enumerate(bpms):
        ts = f"2024-01-01T09-{i:02d}-00"
        fname = os.path.join(args.folder, f"MEA_test_{ts}.h5")
        _write_h5(fname, bpm_e71=bpm, bpm_e84=bpm * 1.05, file_idx=i)
        print(f"  {os.path.basename(fname)}  (E71={bpm:.1f} bpm, E84={bpm*1.05:.1f} bpm)")

    print(f"\nRun analysis:")
    print(f"  python run_mea_analysis.py {args.folder} "
          f"--electrodes 71 84 --max-bpm 40 --report report.html --output-db results.duckdb")


if __name__ == "__main__":
    main()
