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

import os
import sys
import optparse


def get_option_parser():
	"""Returns initialized OptionParser object"""
	p = optparse.OptionParser(usage="%prog [options] [mapfile]")
	p.add_option("--fife-path", dest="fife_path", metavar="<path>", \
				       help=_("Specify the path to FIFE root directory."))

	return p

if __name__ == '__main__':
	# prepare sys path and init UH
	def up(path):
		return os.path.split(path)[0]
	uh_path = up(up(os.path.realpath(sys.argv[0])))
	sys.path.append(uh_path)
	from run_uh import init_environment, get_fife_path
	init_environment()

	# append again in case init_environment() restarts
	uh_path = up(up(os.path.realpath(sys.argv[0])))
	sys.path.append(uh_path)

	(options, argv) = get_option_parser().parse_args()
	editor_path = get_fife_path(options.fife_path) + '/tools/editor'
	os.chdir(editor_path)
	sys.path.append(editor_path)

	# Start editor
	class MockOptions:
		plugin_dir = uh_path + '/editor/plugins'
	options = MockOptions()
	mapfile = None
	if argv:
		mapfile = argv[0]

	from scripts.editor import Editor, TDS
	# force UH plugins to be enabled
	TDS.set("Plugins", "UHObjectLoader", True)
	TDS.set("Plugins", "UHMapLoader", True)
	TDS.set("Plugins", "UHMapSaver", True)
	app = Editor(options, mapfile)
	app.run()


