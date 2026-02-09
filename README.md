# DatAnalyzer (Python)
**Notice**: This is a Python version of [DatAnalyzer](https://github.com/AnaHill/DatAnalyzer) tool. AI Assistant (Cursor) is heavy used in this transformation. _Under development_.

Tools to load, visualize, and analyse Multi-Electrode Array (MEA) field potential data using Python.

DatAnalyzer provides flexible, customizable semi-autonomous data analysis: good automatic settings to detect most peaks from large datasets, and the ability to refine results (e.g. add or remove peaks) programmatically or via future GUI tools.

**Data format:** MEA HDF5 (.h5) files. Measurement files must be converted to HDF5 first; for Multichannel Systems devices, use [MultiChannel Data Manager](https://www.multichannelsystems.com/software/multi-channel-datamanager#docs).

## Features

- **Load raw MEA data** from Multichannel Systems HDF5 (.h5) files
- **MEA layout**: read electrode layout and map electrode numbers to data columns
- **Peak finding**: semi-autonomous peak detection (low/high) with configurable rules (MinPeakValue, MaxBPM, MinPeakDistance)
- **BPM update**: peak-to-peak distances (ms), BPM per file/electrode, low vs high peak choice per channel
- **BPM summary**: Amount_of_peaks, BPM_avg, Amplitude_avg, normalizing, peak_distances

## Requirements

- Python 3.8+
- numpy, scipy, h5py, pandas, matplotlib

## Installation

```bash
git clone <your-repo-url> DatAnalyzer-Python
cd DatAnalyzer-Python
pip install -r requirements.txt
```

Optional, install as a package:

```bash
pip install -e .
```

## Project layout

```
DatAnalyzer-Python/
├── README.md
├── requirements.txt
├── pyproject.toml
├── run_mea_analysis.py       # Example: load → find peaks → BPM summary
├── mea_layouts/
│   └── MEA_64_electrode_layout.txt
└── datanalyzer/
    ├── __init__.py
    ├── models.py
    ├── part1_raw_data_handling/   # HDF5 load, MEA layout
    ├── part2_peak_handling/       # find_peaks_in_loop, rules
    └── part3_data_handling_and_analyses/  # update_Data_BPM, create_BPM_summary
```

## Usage

### Command line

```bash
python run_mea_analysis.py /path/to/h5/folder --electrodes 21 28 31 51 --max-bpm 40 --min-peak-value 5e-5
```

### From Python

```python
from datanalyzer.part1_raw_data_handling import load_raw_mea_data_to_Data_and_DataInfo
from datanalyzer.part2_peak_handling import find_peaks_in_loop, set_default_filetype_rules_for_peak_finding
from datanalyzer.part3_data_handling_and_analyses import update_Data_BPM, create_BPM_summary

Data, DataInfo = load_raw_mea_data_to_Data_and_DataInfo(
    folder_of_files="/path/to/h5/folder",
    manually_chosen_mea_electrodes=[21, 28, 31, 51],
)
Rule = set_default_filetype_rules_for_peak_finding(frame_rate=float(DataInfo.framerate.flat[0]))
Rule.max_bpm = 40
Rule.min_peak_value = 5e-5
DataInfo.Rule = Rule
Data_BPM = find_peaks_in_loop(Data, DataInfo, Rule_in=Rule, data_multiply=-1)
Data_BPM = update_Data_BPM(DataInfo, Data_BPM, using_high_peaks=-1)
Data_BPM_summary = create_BPM_summary(DataInfo, Data_BPM)
```

## Citations

DatAnalyzer has been developed at Tampere University (TAU) in the [Micro- and Nanosystems Research Group](https://research.tuni.fi/mst/) (MST). If you find it useful, please consider citing:

- Mäki, A.-J. (2023). Opinion: The correct way to analyze FP signals. Zenodo. https://doi.org/10.5281/zenodo.10205591

## License

See LICENSE file in the repository.
