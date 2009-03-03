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

if ! [ -d "$1" ]; then 
	echo "You must specify a FIFE dir!"
	exit 1
fi
if ! [ -d "$2" ]; then 
	echo "You must specify a Unknown Horizons dir!"
	exit  1
fi




fife=$1
echo "Using ${fife} as FIFE dir."
uh=$2
echo "Using ${uh} as Unknown Horizons dir."

# Find all .so files
echo "Searching for .so FIFE files..."
files=$(find ${fife} -type f -name *.so)
echo "Done. Copying files to Unknown Horizons dir..."
cp --parents ${files}  -t ${uh}
echo "Done."

echo "Copying ext/ to Unknown Horizons dir..."
cp --parents -r ${fife}/ext/install/ -t ${uh}
echo "Done."

# Find all engine .py files
echo "Searching for engine .py FIFE files..."
files=$(find ${fife}/engine/ -type f -name *.py)
echo "Done. Copying files to Unknown Horizons dir..."
cp --parents ${files}  -t ${uh}
echo "Done."

echo "Adding editor..."
cp -r --parents ${fife}/clients/editor -t ${uh}
echo "Done."

echo "Adding docs..."
cp -r --parents ${fife}/doc/AUTHORS -t ${uh}
cp -r --parents ${fife}/doc/README -t ${uh}
cp -r --parents ${fife}/doc/COPYING -t ${uh}
echo "Done."

echo "Creating Tarball ${3}..."
if ! [ -z $3 ]; then 
	tar -cf ${3} ${uh}
else
	tar -cf unknown-horizonz$(date +"%m%d%y").tar ${uh}
fi
echo "Done."

echo "Release tarball is ready for deployment."
