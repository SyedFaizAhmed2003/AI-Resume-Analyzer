@echo off
echo ========================================================
echo AI Resume Analyzer - Clean Modern API Setup
echo ========================================================

echo.
echo [1/5] Creating Python 3.10 Virtual Environment (venvapp)...
py -3.10 -m venv venvapp
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to create virtual environment. Ensure you have Python 3.10 installed and in PATH.
    pause
    exit /b 1
)

echo.
echo [2/5] Installing Backend Dependencies...
call venvapp\Scripts\activate.bat
cd App
pip install -r requirements.txt
cd ..

echo.
echo [3/5] Downloading spaCy model (en_core_web_sm)...
python -m spacy download en_core_web_sm

echo.
echo [4/5] Applying pyresparser hacks/patches automatically...
python patch_env.py

echo.
echo [5/5] Setup Complete!
echo ========================================================
echo The environment is fully configured!
echo To run the application, just double-click: run.bat
echo ========================================================
pause
