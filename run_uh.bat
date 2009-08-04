@echo off
echo Starting Unknown Horizons
echo output will be written to logfile "unknownhorizons-DATETIME.log"
echo errors will be written to logfile "unknownhorizons.error.log"
run_uh.py -d 2>unknownhorizons.error.log
pause
