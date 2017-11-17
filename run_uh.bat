@echo off
echo Starting Unknown Horizons
if '%1' == '--debug' goto debugMode
if '%1' == '--help' goto help

echo output will be written to logfile "unknownhorizons-DATETIME.log"
IF EXIST ..\python\python.exe (
  ..\python\python.exe run_uh.py --debug-log-only
) ELSE (
  run_uh.py --debug-log-only
)
pause
goto:EOF

:debugMode
IF EXIST ..\python\python_d.exe (
  ..\python\python_d.exe run_uh.py --debug-log-only
) ELSE (
  run_uh.py --debug-log-only
)
if errorlevel 1 (echo.
echo Error! Please check if you have Python Debug installed!
echo.)
pause
goto:EOF

:help
echo '--debug': Debug mode. Needs Python debug with FIFE debug compiled.
echo '--help': Display Help information.
