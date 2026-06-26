"""Generate a self-contained HTML report from MEA analysis results."""

import io
import os
from typing import Any, List, Optional
import numpy as np


def generate_html_report(
    DataInfo: Any,
    Data_BPM_summary: dict,
    output_path: Optional[str] = "report.html",
) -> str:
    """
    Build a single self-contained HTML file with charts (inline SVG via matplotlib)
    and a summary table.  No CDN or external resources needed.

    Returns the HTML as a string and writes it to output_path if provided.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    electrodes = DataInfo.MEA_electrode_numbers
    n_files = DataInfo.files_amount
    file_labels = _file_labels(DataInfo, n_files)

    bpm = Data_BPM_summary["BPM_avg"]
    amp_uv = Data_BPM_summary["Amplitude_avg"] * 1e6
    peak_counts = Data_BPM_summary["Amount_of_peaks"]
    bpm_norm = Data_BPM_summary.get("BPM_norm")
    amp_norm = Data_BPM_summary.get("Amplitude_norm")

    bpm_svg = _line_chart(plt, bpm, file_labels, electrodes, "BPM Average per File", "BPM")
    amp_svg = _line_chart(plt, amp_uv, file_labels, electrodes, "Amplitude Average per File", "Amplitude (µV)")

    norm_section = ""
    if bpm_norm is not None and amp_norm is not None:
        norm_bpm_svg = _line_chart(plt, bpm_norm, file_labels, electrodes, "BPM Normalised", "BPM norm")
        norm_amp_svg = _line_chart(plt, amp_norm, file_labels, electrodes, "Amplitude Normalised", "Amplitude norm")
        norm_section = f"""
<h2>Normalised Values</h2>
{norm_bpm_svg}
{norm_amp_svg}
"""

    summary_table = _summary_table(file_labels, electrodes, bpm, amp_uv, peak_counts)

    fs = float(DataInfo.framerate.flat[0]) if DataInfo.framerate.size > 0 else 0.0
    html = _build_html(
        exp_name=DataInfo.experiment_name,
        meas_name=DataInfo.measurement_name,
        meas_date=DataInfo.measurement_date,
        framerate=fs,
        bpm_svg=bpm_svg,
        amp_svg=amp_svg,
        norm_section=norm_section,
        summary_table=summary_table,
    )

    if output_path:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"  Report written to: {os.path.abspath(output_path)}")

    return html


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _file_labels(DataInfo: Any, n_files: int) -> List[str]:
    if DataInfo.file_names:
        return [os.path.basename(fn) for fn in DataInfo.file_names]
    return [f"File {i + 1}" for i in range(n_files)]


def _line_chart(plt, data: np.ndarray, file_labels: List[str], electrodes: List[int], title: str, ylabel: str) -> str:
    fig, ax = plt.subplots(figsize=(10, 4))
    x = list(range(len(file_labels)))
    n_cols = data.shape[1] if data.ndim > 1 else 0
    for ci, elec in enumerate(electrodes):
        if ci >= n_cols:
            break
        col = data[:, ci]
        ax.plot(x, col, marker="o", linewidth=1.5, markersize=4, label=f"E{elec}")
    ax.set_xticks(x)
    ax.set_xticklabels(file_labels, rotation=40, ha="right", fontsize=7)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.legend(loc="upper right", fontsize=7, ncol=max(1, len(electrodes) // 6))
    ax.grid(True, alpha=0.25, linestyle="--")
    plt.tight_layout()
    svg = _fig_to_svg(fig)
    plt.close(fig)
    return svg


def _fig_to_svg(fig) -> str:
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    content = buf.getvalue()
    return content[content.find("<svg"):]


def _fmt(v, spec: str = ".2f") -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return format(float(v), spec)


def _summary_table(
    file_labels: List[str],
    electrodes: List[int],
    bpm: np.ndarray,
    amp_uv: np.ndarray,
    peak_counts: np.ndarray,
) -> str:
    header = (
        "<tr>"
        "<th>#</th><th>File</th><th>Electrode</th>"
        "<th>BPM avg</th><th>Amplitude (µV)</th><th>Peaks</th>"
        "</tr>"
    )
    rows = []
    n_cols = bpm.shape[1] if bpm.ndim > 1 else 0
    for fi, flabel in enumerate(file_labels):
        for ci, elec in enumerate(electrodes):
            if ci >= n_cols:
                break
            b = bpm[fi, ci]
            a = amp_uv[fi, ci]
            n = peak_counts[fi, ci]
            rows.append(
                f"<tr>"
                f"<td>{fi + 1}</td><td class='left'>{flabel}</td><td>{elec}</td>"
                f"<td>{_fmt(b)}</td><td>{_fmt(a)}</td><td>{_fmt(n, '.0f')}</td>"
                f"</tr>"
            )
    return f"<table>{header}{''.join(rows)}</table>"


def _build_html(
    exp_name: str,
    meas_name: str,
    meas_date: str,
    framerate: float,
    bpm_svg: str,
    amp_svg: str,
    norm_section: str,
    summary_table: str,
) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DatAnalyzer — {exp_name} / {meas_name}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: Arial, sans-serif; margin: 0; padding: 1.5rem 2rem; color: #222; background: #fafafa; }}
  h1 {{ color: #1a5276; margin-bottom: 0.25rem; }}
  h2 {{ color: #1f618d; margin-top: 2rem; border-bottom: 2px solid #aed6f1; padding-bottom: 0.25rem; }}
  .meta {{ background: #eaf2fb; border-left: 4px solid #2980b9; padding: 0.75rem 1rem;
           border-radius: 3px; margin: 0.75rem 0 1.5rem; font-size: 0.95rem; }}
  .meta span {{ margin-right: 1.5rem; }}
  .meta strong {{ color: #1a5276; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 0.75rem; font-size: 0.9rem; }}
  th, td {{ border: 1px solid #d5d8dc; padding: 5px 9px; text-align: right; }}
  th {{ background: #2980b9; color: #fff; font-weight: 600; }}
  td.left {{ text-align: left; }}
  tr:nth-child(even) td {{ background: #f2f3f4; }}
  .chart-wrap {{ background: #fff; border: 1px solid #d5d8dc; border-radius: 4px;
                 padding: 0.5rem; margin-top: 0.5rem; overflow-x: auto; }}
  svg {{ max-width: 100%; height: auto; display: block; }}
</style>
</head>
<body>
<h1>DatAnalyzer MEA Report</h1>
<div class="meta">
  <span><strong>Experiment:</strong> {exp_name}</span>
  <span><strong>Measurement:</strong> {meas_name}</span>
  <span><strong>Date:</strong> {meas_date}</span>
  <span><strong>Framerate:</strong> {framerate:.0f} Hz</span>
</div>

<h2>BPM Over Files</h2>
<div class="chart-wrap">{bpm_svg}</div>

<h2>Amplitude Over Files</h2>
<div class="chart-wrap">{amp_svg}</div>
{norm_section}
<h2>Summary Table</h2>
{summary_table}
</body>
</html>
"""
