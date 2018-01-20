#!/usr/bin/env python

# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

# usage:
# copy the full content/ folder into src/Contents/Resources/
# moreover copy the fife dir into the current dir
# details can be found at http://wiki.unknown-horizons.org/w/MacOS_build_notes

import os

from setuptools import setup

# Sets what directory to crawl for files to include
# Relative to location of setup.py; leave off trailing slash
includes_dir = 'content'

# Set the root directory for included files
# Relative to the bundle's Resources folder, so '../../' targets bundle root
includes_target = 'content/'

# Initialize an empty list so we can use list.append()
data_includes = []

# Walk the includes directory and include all the files
for root, dirs, filenames in os.walk(includes_dir):
    if root is includes_dir:
        final = includes_target
    else:
        final = includes_target + root[len(includes_dir) + 1:] + '/'
    files = []
    for file in filenames:
        if (file[0] != '.'):
            files.append(os.path.join(root, file))
    data_includes.append((final, files))

packages = []
packages.append('horizons')
packages.append('fife')

#Info.plist keys for the app
#Icon.icns must be inside src/Contents/Resources/
plist = {"CFBundleIconFile": "content/gui/icons/Icon.icns",
		 "CFBundleDisplayName": "Unknown Horizons",
		 "CFBundleExecutable": "Unknown Horizons",
		 "CFBundleIdentifier": "org.unknown-horizons",
		 "CFBundleName": "Unknown Horizons",
		 "CFBundleShortVersionString": "0.0.0",
		 "LSArchitecturePriority": ["x86_64", "i386"],
		 "CFBundleVersion": "0.0.0"
		}

APP = ['run_uh.py']
OPTIONS = {'argv_emulation': True, 'packages': packages, 'plist': plist}

setup(
    app=APP,
    data_files=data_includes,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
