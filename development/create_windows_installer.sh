#!/bin/bash

RELEASE_VERSION=2013.3

PYTHON_DIR="C:/Python27"
PYTHON_DLL="C:/windows/system32/python27.dll"

BUILD_DIR="../../build/build_$(date +%Y%m%d%H%M)"
echo "Creating build folder: $BUILD_DIR"
mkdir -p $BUILD_DIR

echo "Copying UH..."
cp -r ../* $BUILD_DIR

PYTHON_TARGET=$BUILD_DIR/python
mkdir -p $PYTHON_TARGET

echo "Copying Python..."
cp -r $PYTHON_DIR/* $PYTHON_TARGET
cp $PYTHON_DLL $PYTHON_TARGET

# go to uh main dir
cd $BUILD_DIR
cd python
rm -r Doc
rm -r Scripts
rm -r tcl
rm -r Tools
rm NEWS.txt
rm Remove*
rm w9xpopen.exe
cd ..

echo "Running Setup..."
cd development
python compile_translation_win.py
python ../horizons/engine/generate_atlases.py 1024
cd ..

echo "Cleaning up"
./development/rmpyc.sh

rm setup*
rm unknown-horizons
rm unknown-horizons.wpr
rm stage_build_mac.py
rm *_tests*
rm -r tests/
rm MANIFEST.in
rm CONTRIBUTING.md
rm run_uh.bat

echo "Unsetting dev version..."
sed -i 's/IS_DEV_VERSION\s=\sTrue/IS_DEV_VERSION = False/g' horizons/constants.py
sed -i "s/RELEASE_VERSION = .*/RELEASE_VERSION = u'$RELEASE_VERSION'/g" horizons/constants.py
sed -i "s/current_version\.php/current_version_win\.php/g" horizons/constants.py

echo "Removing non-atlas graphics..."
rm -r content/gfx/{base,buildings,units,terrain}

echo "Creating executable..."
echo -e "python\pythonw.exe run_uh.py\r\npause" > unknown-horizons.bat
echo -e "python\python.exe run_uh.py --debug-log-only\r\npause" > unknown-horizons-debug.bat

cd development
python nsiscripter.py $RELEASE_VERSION
cd ..

makensis install.nsi
mv Setup.exe unknown-horizons-${RELEASE_VERSION}_win32.exe

echo "Done!"
