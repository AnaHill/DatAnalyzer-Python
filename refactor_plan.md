# Refactor
Consider refactor this repo.
Idea would be, if possible and useful
- use duckdb as an OLAP and python
- html or other as frontend
- minimize installing anything

Suggested workflow
- go through this repo
- if needed, check original DatAnalyzer MATLAB repo, https://github.com/AnaHill/DatAnalyzer
- Plan before action, the next steps

# GUI options
Option A — Streamlit (recommended)
pip install streamlit — one new dependency, runs in the browser.

File/folder picker, sliders for BPM/threshold, electrode list → Run button
Results appear immediately in the same page: matplotlib charts via st.pyplot(), summary table via st.dataframe()
Download buttons for the HTML report and DuckDB file
Reuses 100% of the existing part4_export / part5_report code
~150 lines in a single app.py at the project root
Launch: streamlit run app.py
Tradeoff: one install, requires a browser, not a native desktop window.

Option B — Tkinter (zero install)
Ships with Python, no pip needed.

Native Windows dialog for folder selection
Form fields for parameters, a Run button, results in a scrollable text area
Matplotlib charts embedded in the window via FigureCanvasTkAgg
Fully offline, no browser
More code (~300 lines), looks dated on Windows 11
Tradeoff: zero installs, but harder to make it look good and harder to show a proper data table.

Option C — FastAPI + the existing HTML report
pip install fastapi uvicorn — two installs.

A tiny REST API serves the pipeline; the existing HTML report becomes the "result page"
Could evolve into a proper web app later
Most work of the three options right now
Recommendation
Streamlit — it's the fastest path to a usable, good-looking UI that reuses what's already built. The single install is justified. If zero installs is a hard requirement, Tkinter is the fallback.

Which direction do you want to go?