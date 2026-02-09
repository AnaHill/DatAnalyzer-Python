"""
MEA electrode layout: read layout file and map electrode numbers to data column indices.
"""

from pathlib import Path
from typing import List, Optional, Union
import pandas as pd
import numpy as np


def read_mea_electrode_layout(
    mea_layout_name: Optional[str] = None,
    mea_folder: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """
    Read MEA layout file (electrode_number, index).
    Default: MEA_64_electrode_layout.txt in repo mea_layouts/ folder.
    Returns DataFrame with columns electrode_number, index (1-based column in raw data).
    """
    if mea_folder is None:
        mea_folder = Path(__file__).resolve().parent.parent.parent / "mea_layouts"
    else:
        mea_folder = Path(mea_folder)
    if mea_layout_name is None:
        mea_layout_name = "MEA_64_electrode_layout.txt"
    path = mea_folder / mea_layout_name
    if not path.exists():
        raise FileNotFoundError(f"MEA layout not found: {path}")
    df = pd.read_csv(path, sep=r"\s+", header=0)
    df = df.drop_duplicates().sort_values(list(df.columns)).reset_index(drop=True)
    return df


def find_mea_electrode_index(
    electrodes_numbers: List[int],
    electrode_layout: Optional[pd.DataFrame] = None,
) -> np.ndarray:
    """
    Map electrode numbers to raw data column indices (1-based).
    electrode_layout must have columns matching the layout file (electrode_number, index).
    """
    if not electrodes_numbers:
        return np.array([], dtype=int)
    if electrode_layout is None:
        electrode_layout = read_mea_electrode_layout()
    el_nums = electrode_layout.iloc[:, 0].values
    el_ind = electrode_layout.iloc[:, 1].values
    out = []
    for en in electrodes_numbers:
        idx = np.where(el_nums == en)[0]
        if len(idx) == 0:
            raise ValueError(f"Electrode number {en} not found in layout.")
        out.append(int(el_ind[idx[0]]))
    return np.array(out, dtype=int)


def read_wanted_electrodes_of_measurement(
    exp_name: str,
    meas_name: str,
    electrode_layout: Optional[pd.DataFrame] = None,
) -> List[int]:
    """
    Return list of electrode numbers for (exp_name, meas_name).
    If no predefined list exists, returns [] so caller must pass manually_chosen_mea_electrodes.
    """
    known = {
        ("MEA2020_03_02", "MEA21002b"): [21, 28, 31, 51],
        ("Exp_11311_EURCCS_p32_180820", "mea21001a"): [44, 71, 75, 84],
        ("Exp_11311_EURCCS_p32_180820", "mea21001b"): [25, 36, 55, 62, 71],
        ("Exp_11311_EURCCS_p32_180820", "mea21002a"): [45, 56, 64, 82],
    }
    key = (exp_name.strip(), meas_name.strip())
    if key in known:
        return list(known[key])
    return []
