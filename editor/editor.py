#!/usr/bin/env python

# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

class DictObj:
	def __init__(self, d):
		self.d = d

	def __getattr__(self, m):
		return self.d.get(m)

if __name__ == '__main__':
	import gettext
	gettext.install('', unicode=True) # necessary for init_environment

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

	editor_path = get_fife_path() + '/tools/editor'
	os.chdir(editor_path)
	sys.path.append(editor_path)

	# Start editor
	options = {'plugin_dir': uh_path + '/editor/plugins'}
	options = DictObj(options)
	mapfile = None
	if len(sys.argv) > 1:
		mapfile = sys.argv[1]
	from scripts.editor import Editor
	app = Editor(options, mapfile)
	app.run()
