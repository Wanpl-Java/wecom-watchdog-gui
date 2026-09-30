@echo off
cd /d "%~dp0"

REM Fix broken Tcl lookup for Python 3.13 installs on D:\
if exist "D:\Python313\tcl\tcl8.6\init.tcl" (
  set "TCL_LIBRARY=D:\Python313\tcl\tcl8.6"
  set "TK_LIBRARY=D:\Python313\tcl\tk8.6"
)
if exist "%LocalAppData%\Programs\Python\Python313\tcl\tcl8.6\init.tcl" (
  set "TCL_LIBRARY=%LocalAppData%\Programs\Python\Python313\tcl\tcl8.6"
  set "TK_LIBRARY=%LocalAppData%\Programs\Python\Python313\tcl\tk8.6"
)

if not exist .venv\Scripts\python.exe (
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
)

REM Prefer desktop Tk GUI; if Tcl still broken, fall back to browser UI
.venv\Scripts\python.exe -c "import os; os.environ.setdefault('TCL_LIBRARY', r'D:\Python313\tcl\tcl8.6'); os.environ.setdefault('TK_LIBRARY', r'D:\Python313\tcl\tk8.6'); import tkinter" 1>nul 2>nul
if errorlevel 1 (
  echo [warn] Tk/Tcl unavailable, starting browser UI on http://127.0.0.1:8765
  .venv\Scripts\python.exe app\web_ui.py
) else (
  .venv\Scripts\python.exe app\main.py
)
