#!/usr/bin/env python3

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

'''
Generate html output for a page displaying all images currently available
in the repository and in a certain directory. Does not wite anything to a
file, you will need to redirect output.
Change `where` below to anything else as you see fit.
'''
from __future__ import print_function

import os
import os.path


# All gui images and icons
where = 'content/gui/'

# All atlas files
# where = 'content/gfx/atlas/'

# All building, unit and other images (including atlas files)
# Warning: This most likely is too huge to be of any help.
# where = 'content/gfx/'

# make this script work both when started inside development and in the uh root dir
if not os.path.exists('content'):
	os.chdir('..')
assert os.path.exists('content'), 'Content dir not found.'

base_url = 'file://localhost/' + os.path.abspath(os.getcwd()) + '/'

for root, dirs, files in sorted(os.walk(where)):
	for f in sorted(files):
		if not f.endswith(('.png', '.jpg')):
			continue
		url = base_url + '/' + root + '/' + f
		print('<a href="{url}"><img src="{url}" /></a>'.format(url=url))
