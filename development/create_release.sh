#!/bin/bash

# ###################################################
# Copyright (C) 2008 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

# This script is used to create Unknown Horizons release tarballs for linux
# It will copy all needed fife files to a 'fife' folder in the Unknown Horizons folder
#
# Please note, in order for a successful run of this script we assume you are in a directory 
# that has two childern fife/ and unknown-horizons/ that you will specifiy. The fife/ folder
# containing the the FIFE svn trunk and the unknown-horizons/ folder containing the 
# Unknown Horizons folder. So you would find: fife/test_fife.py and unknown-horizons/run_uh.py


if [ -z $1 ]; then 
	echo "Usage:"
	echo "${0} <fife dir> <unknown-horizons dir> [tarballname]" 
	exit 1
fi

if ! [ -d "$1" ] && [ -e "$1/test_fife.py"] ; then 
	echo "You must specify a FIFE dir (must contain test_fife.py)!"
	exit 1
fi
if ! [ -d "$2" ] && [ -e "$2/run_uh.py"]; then 
	echo "You must specify a Unknown Horizons dir (must contain run_uh.py)!"
	exit  1
fi

startdir=$(pwd)

fife=$(pwd)/fife_export_$(date +"%m%d%y")
echo "Creating a clean FIFE checkout in ${fife}..."
svn export $1 $fife
echo "Done."

uhfolder=uh_export_$(date +"%m%d%y")
echo $uhfolder
uh="$(pwd)/${uhfolder}"
echo $uh
echo "Creating a clean Unknown Horizons checkout in ${uh}..."
svn export $2 ${uh}
mkdir ${uh}/fife
echo "Done."

# Go into fife dir
cd ${fife}

echo "Compiling FIFE..."
scons ext=1
scons debug=0 log=0
echo "Done..."

# Find all .so files
echo "Searching for .so FIFE files..."
files=$(find . -type f -name \*.so)
echo "Done. Copying files to Unknown Horizons dir..."
cp --parents ${files}  -t ${uh}/fife/
rm -r ${uh}/fife/ext/openal-soft/
echo "Done."

echo "Copying ext/ to Unknown Horizons dir..."
cp --parents -r ext/install/ -t ${uh}/fife/
echo "Done."

# Find all engine .py files
echo "Searching for engine .py FIFE files..."
files=$(find engine/ -type f -name \*.py)
echo "Done. Copying files to Unknown Horizons dir..."
cp --parents ${files}  -t ${uh}/fife/
echo "Done."

echo "Adding editor..."
cp -r --parents clients/editor -t ${uh}/fife/
echo "Done."

echo "Adding docs..."
cp -r --parents doc/AUTHORS -t ${uh}/fife/
cp -r --parents doc/README -t ${uh}/fife/
cp -r --parents doc/COPYING -t ${uh}/fife/
echo "Done."

# Go back to startdir
cd ${startdir}

echo "Creating Tarball ${3}..."
if ! [ -z $3 ]; then 
	tar -xcf ${3} ${uhfolder}
else
	tar -xcf unknown-horizonz$(date +"%m%d%y").tar.gz ${uhfolder}

fi
echo "Done."

echo "Cleaning up..."
rm -r ${uh}
rm -r ${fife}

echo "Release tarball is ready for deployment."

