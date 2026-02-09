"""
DatAnalyzer - MEA data analysis in Python.

Load, visualize, and analyze Multi-Electrode Array (MEA) field potential data
from HDF5 (.h5) files. Semi-autonomous peak finding and BPM analysis.
"""

__version__ = "0.1.0"

from datanalyzer.models import DataInfo, Rule, PeakRule

__all__ = ["DataInfo", "Rule", "PeakRule", "__version__"]
