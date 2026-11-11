#!/bin/bash

set -e

RELEASE_VERSION=2019.1

BUILD_DIR="../../build/build_$(date +%Y%m%d%H%M)/unknown-horizons"
echo "Creating build folder: $BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "Copying UH..."
cp -r ../* "$BUILD_DIR"

# go to uh main dir
cd "$BUILD_DIR" || exit

cd content/gfx || exit
rm -rf atlas/*
cd ..
rm -f atlas.sql
rm -f actionsets.json
rm -f tilesets.json
cd ..


echo "Running Setup..."
cd development || exit
python3 compile_translation_win.py
python3 ../horizons/engine/generate_atlases.py 1024
cd ..

echo "Cleaning up..."
./development/rmpyc.sh

rm -f unknown-horizons.wpr
rm -f stage_build_mac.py
rm -rf ./_tests*
rm -rf tests/
rm -f CONTRIBUTING.md
rm -f run_uh.bat

# These files/directories may or may not be present
rm -rf __pycache__
rm -f po/*/*.po~
rm -f po/scenarios/*/*.po~

echo "Unsetting dev version..."
sed -i 's/IS_DEV_VERSION\s=\sTrue/IS_DEV_VERSION = False/g' horizons/constants.py
sed -i "s/RELEASE_VERSION = .*/RELEASE_VERSION = u'$RELEASE_VERSION'/g" horizons/constants.py

echo "Removing non-atlas graphics..."
rm -rf content/gfx/{base,buildings,units,terrain}

echo "Creating archive.."
cd ..
tar -c --xz -f unknown-horizons-${RELEASE_VERSION}.tar.xz unknown-horizons/

echo "Done!"
