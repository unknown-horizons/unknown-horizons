#!/bin/bash

RELEASE_VERSION=2019.1

BUILD_DIR="../../build/build_$(date +%Y%m%d%H%M)/unknown-horizons"
echo "Creating build folder: $BUILD_DIR"
mkdir -p $BUILD_DIR

echo "Copying UH..."
cp -r ../* $BUILD_DIR

# go to uh main dir
cd $BUILD_DIR

cd content/gfx
rm -r atlas/*
cd ..
rm -f atlas.sql
rm -f actionsets.json
rm -f tilesets.json
cd ..


echo "Running Setup..."
cd development
python3 compile_translation_win.py
python3 ../horizons/engine/generate_atlases.py 1024
cd ..

echo "Cleaning up..."
./development/rmpyc.sh

rm unknown-horizons.wpr
rm stage_build_mac.py
rm *_tests*
rm -r tests/
rm CONTRIBUTING.md
rm run_uh.bat

# These files/directories may or may not be present
rm -r __pycache__
rm po/*/*.po~
rm po/scenarios/*/*.po~

echo "Unsetting dev version..."
sed -i 's/IS_DEV_VERSION\s=\sTrue/IS_DEV_VERSION = False/g' horizons/constants.py
sed -i "s/RELEASE_VERSION = .*/RELEASE_VERSION = u'$RELEASE_VERSION'/g" horizons/constants.py

echo "Removing non-atlas graphics..."
rm -r content/gfx/{base,buildings,units,terrain}

echo "Creating archive.."
cd ..
tar -c --xz -f unknown-horizons-${RELEASE_VERSION}.tar.xz unknown-horizons/

echo "Done!"
