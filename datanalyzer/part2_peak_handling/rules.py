"""
Default peak-finding rules for MEA/other signal types.
"""

from datanalyzer.models import Rule


def set_default_filetype_rules_for_peak_finding(
    frame_rate: float = 25e3,
    signal: str = "MEA",
) -> Rule:
    """Return default Rule for peak finding. MEA: low peaks, MaxBPM 120, MinPeakValue 2.5e-5."""
    if signal == "MEA":
        return Rule(
            frame_rate=frame_rate,
            signal=signal,
            is_low_peaks_counted=1,
            minimum_peak_width=50,
            max_bpm=120.0,
            min_peak_value=2.5e-5,
        )
    if signal == "CA":
        return Rule(
            frame_rate=frame_rate,
            signal=signal,
            is_low_peaks_counted=0,
            minimum_peak_width=50,
            max_bpm=180.0,
            min_peak_value=5.0,
        )
    if signal == "AP":
        return Rule(
            frame_rate=frame_rate,
            signal=signal,
            is_low_peaks_counted=0,
            minimum_peak_width=50,
            max_bpm=180.0,
            min_peak_value=400.0,
        )
    return Rule(
        frame_rate=frame_rate,
        signal=signal,
        max_bpm=120.0,
        min_peak_value=2.5e-5,
    )
