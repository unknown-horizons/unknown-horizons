#!/usr/bin/env python

# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

import os
import sys
import openanno

if __name__ == '__main__':
	#chdir to openanno root
	os.chdir( os.path.split( os.path.realpath( sys.argv[0]) )[0] )

	#find fife and setup search paths
	fife_path = openanno.getFifePath()

	#for some external libraries distributed with openanno
	os.environ['PYTHONPATH'] = os.path.pathsep.join((os.path.abspath('editor'), os.path.abspath('game'), os.path.abspath('game/ext'), os.environ['PYTHONPATH']))

	os.chdir(fife_path + '/clients/editor')
	#start editor
	args = [sys.executable, './run.py']
	os.execvp(args[0], args)
