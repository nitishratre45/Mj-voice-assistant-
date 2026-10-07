@echo off
setlocal
cd /d "%~dp0"

set "PY=python"
where py >nul 2>&1 && set "PY=py -3"

%PY% -u brain.py
if errorlevel 1 (
  echo.
  echo MJ failed to start. Check the error above.
  pause
)
endlocal
