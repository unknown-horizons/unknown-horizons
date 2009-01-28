@echo off
set datetime=%date%_%time%
set datetime=%datetime: =0%
set datetime=%datetime:.=-%
set datetime=%datetime:,=-%
set datetime=%datetime::=-%
echo starting openanno, output will be written into logfile "openanno-%datetime%.log"
openanno.py >openanno-%datetime%.log 2>&1
pause