"""
Data structures for MEA analysis (DataInfo, Rule, Data/Data_BPM concepts).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np


@dataclass
class Rule:
    """Peak-finding rules (set_default_filetype_rules_for_peak_finding)."""
    frame_rate: float = 25e3
    signal: str = "MEA"
    is_low_peaks_counted: int = 1
    minimum_peak_width: int = 50
    max_bpm: float = 120.0
    min_peak_value: float = 2.5e-5  # V, 25 µV typical MEA
    min_dist_sec: Optional[float] = None
    min_dist_frames: Optional[float] = None

    def __post_init__(self):
        if self.min_dist_sec is None:
            self.min_dist_sec = 60.0 / self.max_bpm
        if self.min_dist_frames is None:
            self.min_dist_frames = self.min_dist_sec * self.frame_rate


@dataclass
class PeakRule(Rule):
    """Alias for Rule used in peak handling."""
    pass


@dataclass
class DataInfo:
    """Metadata for the dataset (experiment, files, framerate, measurement time)."""
    experiment_name: str = ""
    measurement_name: str = ""
    measurement_date: str = ""
    folder_raw_files: str = ""
    file_names: List[str] = field(default_factory=list)
    files_amount: int = 0
    file_type: str = ".h5"
    electrode_layout: Optional[Any] = None
    MEA_electrode_numbers: List[int] = field(default_factory=list)
    MEA_columns: List[int] = field(default_factory=list)
    datacol_numbers: List[int] = field(default_factory=list)
    framerate: np.ndarray = field(default_factory=lambda: np.array([]))
    measurement_time: Dict[str, Any] = field(default_factory=lambda: {
        "datetime": [],
        "duration": [],
        "time_sec": [],
        "names": [],
    })
    Rule: Optional[Rule] = None
    hypoxia: Optional[Dict[str, Any]] = None
    irregular_beating_limit: float = 0.2

    @property
    def n_files(self) -> int:
        return self.files_amount or len(self.file_names)
