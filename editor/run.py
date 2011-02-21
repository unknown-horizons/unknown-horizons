#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2009 by the FIFE team
#  http://www.fifengine.de
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

import sys, os, re
import optparse

#--- Main function ---#
if __name__ == '__main__':

	p = optparse.OptionParser(usage="%prog [options] <map>", version="development")
	p.add_option("--plugin-dir", dest="plugin_dir", default=None, \
	             help="specify additional plug-in directory")

	(options, args) =  p.parse_args()

	# Get command line arguments
	mapfile = None
	if len(args) >= 1:
		mapfile = args[0]

	# Start editor
	from scripts.editor import Editor
	app = Editor(options, mapfile)
	app.run()
