@echo off
echo DatAnalyzer - Python environment setup
echo =======================================

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Creating virtual environment in .venv\...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

echo Activating environment and installing dependencies...
call .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Setup complete.
echo.
echo To activate the environment in a new terminal:
echo   PowerShell:  .venv\Scripts\activate.bat
echo   cmd:         .venv\Scripts\activate.bat
echo.
echo   (If PowerShell blocks .ps1 scripts, run once as admin:)
echo   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
echo.
echo To launch the web UI:
echo   streamlit run app.py
echo.
echo To generate synthetic test data and run an analysis:
echo   python create_test_data.py
echo   python run_mea_analysis.py test_data --electrodes 71 84 --max-bpm 40 --report report.html
echo.
pause
