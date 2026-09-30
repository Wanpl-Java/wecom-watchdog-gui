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

REM Default: cyber HUD browser UI (more reliable + better visuals)
REM Set USE_DESKTOP=1 to force Tk/customtkinter window instead.
if /I "%USE_DESKTOP%"=="1" (
  echo [info] starting desktop Tk UI
  .venv\Scripts\python.exe app\main.py
) else (
  echo [info] starting cyber HUD on http://127.0.0.1:8765
  .venv\Scripts\python.exe app\web_ui.py
)
