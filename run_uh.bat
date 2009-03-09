@echo off
set datetime=%date%_%time%
set datetime=%datetime:/=_%
set datetime=%datetime: =_%
set datetime=%datetime:.=-%
set datetime=%datetime:,=-%
set datetime=%datetime::=-%
echo Starting Unknown Horizons, output will be written into logfile "unknownhorizons-%datetime%.log"
run_uh.py >unknownhorizons-%datetime%.log 2>&1
pause