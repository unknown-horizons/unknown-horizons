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

"""This is the Unknown Horizons launcher, it looks for fife and tries to start the game. If you want to digg
into the game, continue to horizons/main.py. Read all docstrings and get familiar with the functions and
attributes. I will mark all tutorial instructions with 'TUTORIAL:'. Have fun :-)"""

import sys
import os
import gettext
import getopt


def get_fife_path():
	"""Returns path to fife engine. Calls sys.exit() if it can't be found."""
	global fife_path
	try:
		import config
		_paths = [config.fife_path]
	except (ImportError, AttributeError):
		_paths = []
	_paths += [ a + '/' + b + '/' + c for a in ('.', '..', '../..') for b in ('.', 'fife', 'FIFE', 'Fife') for c in ('.', 'trunk') ]

	fife_path = None
	for p in _paths:
		if p not in sys.path:
			# check if we are in a fife dir...
			for pe in [ os.path.abspath(p + '/' + a) for a in ('.', 'engine', 'engine/extensions', 'engine/swigwrappers/python') ]:
				if not os.path.exists(pe):
					break
			else:
				fife_path = p
				print "Found FIFE in", fife_path

				#add python paths (<fife>/engine/extensions <fife>/engine/swigwrappers/python)
				for pe in [ os.path.abspath(fife_path + '/' + a) for a in ('engine/extensions', 'engine/swigwrappers/python') ]:
					if os.path.exists(pe):
						sys.path.append(pe)
				os.environ['PYTHONPATH'] = os.path.pathsep.join(os.environ.get('PYTHONPATH', '').split(os.path.pathsep) + [ os.path.abspath(fife_path + '/' + a) for a in ('engine/extensions', 'engine/swigwrappers/python') ])

				#add windows paths (<fife>/.)
				os.environ['PATH'] = os.path.pathsep.join(os.environ.get('PATH', '').split(os.path.pathsep) + [ os.path.abspath(fife_path + '/' + a) for a in ('.') ])
				os.path.defpath += os.path.pathsep + os.path.pathsep.join([ os.path.abspath(fife_path + '/' + a) for a in ('.') ])
				break
	else:
		print _('FIFE was not found.')
		exit()
	return fife_path

def find_FIFE():
	"""Inserts path to fife engine to $LD_LIBRARY_PATH (environment variable).
	If it's already there, the function will return, else
	it will restart uh with correct $LD_LIBRARY_PATH. """
	global fife_path

	if fife_path is None:
		fife_path = get_fife_path() # terminates program if fife can't be found

	try:
		if not os.environ.get('LD_LIBRARY_PATH', '').startswith(os.path.abspath(fife_path)):
			try:
				import fife
			except ImportError, e:
				os.environ['LD_LIBRARY_PATH'] = os.path.pathsep.join( \
					[ os.path.abspath(fife_path + '/' + a) for  \
						a in ('ext/minizip', 'ext/install/lib') ] + \
					  (os.environ['LD_LIBRARY_PATH'].split(os.path.pathsep) if \
						 os.environ.has_key('LD_LIBRARY_PATH') else []))

				print "Restarting with proper LD_LIBRARY_PATH..."
				args = [sys.executable] + sys.argv + [ "--fife-path", fife_path ]
				#we are already in Unknown Horizons root, so just exec local executeable
				args[1] = os.path.split(os.path.realpath(args[1]))[1]
				# support for python -O flag (disables __debug__)
				if not __debug__:
					args.insert(1, '-O')
				os.execvp(args[0], args)
		else:
			import fife
	except ImportError, e:
		print _('FIFE was not found or failed to load.')
		print _('Reason: %s') % e.message
		exit()


def print_help():
	print "Unknown Horizons usage:"
	print "run_uh.py [-d] [-h]"
	print ""
	print "Options:"
	print "-d --debug   - Debug, enables debug output, useful for testing."
	print "-h --help    - Print this help message."
	print ""
	print "Have fun playing, and if you do, help us developing!"


if __name__ == '__main__':
	global fife_path

	# parse arguments
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hd", ["help", "debug", "fife-path="])
	except getopt.GetoptError, err:
		print str(err)
		print_help()
		exit(1)

	debug = False
	fife_path = None

	# apply arguments
	for o, a in opts:
		if o in ("-h", "--help"):
			print_help()
			exit(1)
		elif o in ("-d", "--debug"):
			debug = True
		elif o == ("--fife-path"):
			# this is currently only for internal use, therefore not in the help message
			fife_path = a

	#chdir to Unknown Horizons root
	os.chdir( os.path.split( os.path.realpath( sys.argv[0]) )[0] )

	gettext.install("unknownhorizons", "po", unicode=1)

	#find fife and setup search paths, if it can't be imported yet
	try:
		import fife
	except:
		print 'Searching for FIFE'
		find_FIFE()

	print _("Launching Unknown Horizons")

	#for some external libraries distributed with unknownhorizons
	sys.path.append('horizons/ext')

	import horizons.main
	horizons.main.debug = debug

	#start unknownhorizons
	horizons.main.start()

	# gettext support will have to wait so make it an no-op for everything not calling unknownhorizons directly
	_ = lambda x: x
