echo off

echo Generating translation files...
python.exe compile_translation_win.py
echo Done!

echo "Generating installer..."
python.exe nsiscripter.py
echo Done!

cp C:\windows\system32\python27.dll C:\release\Python27\python27.dll


IF NOT EXIST "%1" GOTO NOFIFE

set eng=\engine
set fineng=%1%eng%
IF NOT EXIST "%fineng%" GOTO NOFIFE

echo FIFE at: %1

IF NOT EXIST "%2" GOTO NOPYTHON
set pyexe=\python.exe
set pyt=%2%pyexe%

IF NOT EXIST "%pyt%" GOTO NOPYTHON

echo Python 2.7 at: %2

SET /P version=Release Version: 
SET /P folder=Path to release folder:

echo Release Version: %version%
echo Creating new release in: %folder%
pause


pause

:NOFIFE
echo FIFE not found at: %1
pause

:NOPYTHON
echo PYTHON not found at: %2
pause

