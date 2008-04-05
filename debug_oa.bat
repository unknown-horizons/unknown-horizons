set fife_path=../fife/trunk

set PYTHONPATH=%fife_path%/engine/swigwrappers/python;%fife_path%/engine/extensions;%fife_path%

set PATH=%PATH%;%fife_path%;F:\Python25;F:\Dokumente und Einstellungen\spq\Desktop\Projekte\FIFE\trunk\build\win32\applications\mingw\bin
gdb --args python openanno.py