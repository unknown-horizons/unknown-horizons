@echo off
set datetime=%date%_%time%
set datetime=%datetime: =0%
set datetime=%datetime:.=-%
set datetime=%datetime:,=-%
set datetime=%datetime::=-%
echo starting unknownhorizons editor, output will be written into logfile "editor-%datetime%.log"
editor.py >editor-%datetime%.log 2>&1
pause