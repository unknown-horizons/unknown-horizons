#!/usr/bin/env python
# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

import bz2
import sys
import os

args = sys.argv[1:]

if not args:
	print "USAGE: "+sys.argv[0]+" map1.sqlite map2.sqlite ... mapx.sqlite"
	print
	print "maps will be saved as \"mapx.map\""
	print "to convert all maps, use \""+sys.argv[0]+" content/maps/*sqlite\""
	sys.exit()

for filename in args:
	if not filename.endswith(".sqlite"):
		print "Invalid filename:",filename
		continue
	infile = None
	try:
		infile = open(filename, "r")
	except IOError as e:
		print "Error:",e.message
		continue

	outfile = open(filename.replace('.sqlite','.map'),'w')
	outfile.write( bz2.compress( infile.read() ) )
