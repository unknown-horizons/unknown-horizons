#!/usr/bin/env python

# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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


"""
If run as main program, debug.py will set up LD_LIBRARY_PATH for program in sys.argv[1:], i.e.
./debug.py foo will run foo with LD_LIBRARY_PATH set for uh, so foo doesn't need to restart
Usefull for debugging, because when run_uh.py restarts, it can't be debugged with gdb.
"./debug.py gdb python --args ./run_uh.py" is the only known way to debug uh with gdb.
"""


if __name__ == '__main__':
	import environment
	import sys
	import os

	import gettext
	gettext.install("unknownhorizons", "po", unicode=1)

	#find fife and setup search paths
	try:
		import fife
	except ImportError, e:
		if "--fife-in-library-path" in sys.argv:
			print 'Failed to load FIFE:', e
			exit(1)
		environment.find_FIFE()
	
	args = sys.argv[1:]
	args.remove("--fife-in-library-path")
	print 'Executing with proper fife path: %s with args %s' % (sys.argv[1], args)
	os.execvp(sys.argv[1], args)
else:
	import inspect
	import horizons.main

	already = []
	def printTree(obj, deep = 0):
		global already
		already.append(obj)
		ignore = ['__builtins__', 'this', 'grounds', '_instances']
		try:
			obj.__dict__
		except:
			print str(obj)
			return
		print str(obj) + ':'
		deep += 1
		for name in obj.__dict__:
			if name.startswith('__') and name.endswith('__'):
				continue
			elif name in ignore:
				continue
			elif inspect.ismodule(obj.__dict__[name]) and not obj.__dict__[name].__file__.startswith('/home'):
				continue
			elif obj.__dict__[name] in already:
				continue
			elif inspect.isfunction(obj.__dict__[name]) or inspect.isclass(obj.__dict__[name]):
				continue
			try:
				obj.__dict__[name].__dict__
				continue
			except:
				pass
			print (deep * ' ') + str(name) + ': ',
			printTree(obj.__dict__[name], deep)
		for name in obj.__dict__:
			if name.startswith('__') and name.endswith('__'):
				continue
			elif name in ignore:
				continue
			elif inspect.ismodule(obj.__dict__[name]) and not obj.__dict__[name].__file__.startswith('/home'):
				continue
			elif obj.__dict__[name] in already:
				continue
			elif inspect.isfunction(obj.__dict__[name]) or inspect.isclass(obj.__dict__[name]):
				continue
			try:
				obj.__dict__[name].__dict__
			except:
				continue
			print (deep * ' ') + str(name) + ': ',
			printTree(obj.__dict__[name], deep)

	from game.command import *
	def cmd(name, *pargs, **kargs):
		game.main.session.manager.execute(eval(name)(*pargs, **kargs))

	print _('Debuging tools usage:')
	print _('import debug (already done): load the tools')
	print _('debug.printTree(<object>):   print a tree of an object (the properties, recursive)')
	print _("debug.cmd('name', *args):    create a command and execute it throught the manager ex: debug.cmd('unit.Move', game.main.session.selected_instance, x, y)")
	print ''
