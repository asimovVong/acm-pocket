@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
py -3 -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>&1
if not errorlevel 1 goto use_py
python -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>&1
if not errorlevel 1 goto use_python
echo Python 3.9+ is required. Please install it from https://www.python.org/downloads/windows/
echo Enable the Python launcher or Add python.exe to PATH, then try again.
pause
exit /b 1

:use_py
py -3 -X utf8 "%~dp0launcher.py" %*
set "acm_result=%errorlevel%"
goto done

:use_python
python -X utf8 "%~dp0launcher.py" %*
set "acm_result=%errorlevel%"

:done
if not "%acm_result%"=="0" pause
exit /b %acm_result%
