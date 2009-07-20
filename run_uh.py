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
import time
import logging
import logging.config
import logging.handlers
import getopt

def log():
	"""Returns Logger"""
	return logging.getLogger("run_uh")

def get_fife_path(fife_custom_path=None):
	"""Returns path to fife engine. Calls sys.exit() if it can't be found."""
	# assemble a list of paths where fife could be located at
	_paths = []
	# check if there is a config file (has to be called config.py)
	try:
		import config
		_paths.append(config.fife_path)
	except (ImportError, AttributeError):
		# no config, check for commandline arg
		if fife_custom_path is not None:
			_paths.append(fife_custom_path)

	# try frequently used paths
	_paths += [ a + '/' + b + '/' + c for \
							a in ('.', '..', '../..') for \
							b in ('.', 'fife', 'FIFE', 'Fife') for \
							c in ('.', 'trunk') ]

	fife_path = None
	for p in _paths:
		if p not in sys.path:
			# check if we are in a fife dir by checking for existence of fife dirs
			for pe in [ os.path.abspath(p + '/' + a) for a in ('.', 'engine', 'engine/extensions', 'engine/swigwrappers/python') ]:
				if not os.path.exists(pe):
					break
			else:
				fife_path = p

				log().debug("Found FIFE in %s", fife_path)

				#add python paths (<fife>/engine/extensions <fife>/engine/swigwrappers/python)
				for pe in \
						[ os.path.abspath(fife_path + os.path.sep + a) for \
							a in ('engine/extensions', 'engine/swigwrappers/python') ]:
					if os.path.exists(pe):
						sys.path.append(pe)
				os.environ['PYTHONPATH'] = os.path.pathsep.join(\
					os.environ.get('PYTHONPATH', '').split(os.path.pathsep) + \
					[ os.path.abspath(fife_path + os.path.sep + a) for a in \
						('engine/extensions', 'engine/swigwrappers/python') ])

				#add windows paths (<fife>/.)
				os.environ['PATH'] = os.path.pathsep.join( \
					os.environ.get('PATH', '').split(os.path.pathsep) + \
					[ os.path.abspath(fife_path + '/' + a) for a in ('.') ])
				os.path.defpath += os.path.pathsep + \
					os.path.pathsep.join([ os.path.abspath(fife_path + '/' + a) for a in ('.') ])
				break
	else:
		print _('FIFE was not found.')
		exit()
	return fife_path

def find_FIFE(fife_custom_path=None):
	"""Inserts path to fife engine to $LD_LIBRARY_PATH (environment variable).
	If it's already there, the function will return, else
	it will restart uh with correct $LD_LIBRARY_PATH. """
	fife_path = get_fife_path(fife_custom_path) # terminates program if fife can't be found

	os.environ['LD_LIBRARY_PATH'] = os.path.pathsep.join( \
		[ os.path.abspath(fife_path + '/' + a) for  \
			a in ('ext/minizip', 'ext/install/lib') ] + \
		  (os.environ['LD_LIBRARY_PATH'].split(os.path.pathsep) if \
			 os.environ.has_key('LD_LIBRARY_PATH') else []))

	log().debug("Restarting with proper LD_LIBRARY_PATH...")
	log().debug("LD_LIBRARY_PATH: %s", os.environ['LD_LIBRARY_PATH'])
	log().debug("PATH: %s", os.environ['PATH'])
	log().debug("PYTHONPATH %s", os.environ['PYTHONPATH'])

	# assemble args (python run_uh.py ..)
	args = [sys.executable] + sys.argv + [ "--fife-in-library-path"]
	#we are already in Unknown Horizons root, so just exec local executeable
	args[1] = os.path.split(os.path.realpath(args[1]))[1]
	os.execvp(args[0], args)

def print_help():
	print _("Unknown Horizons usage:")
	print "run_uh.py [-d] [-h]"
	print ""
	print _("Options:")
	print "-d --debug   - ", _("Debug, enables debug output, useful for testing.")
	print "-h --help    - ", _("Print this help message.")
	print ""
	print "--start-dev-map   - ", _("Starts the development map without displaying the main menu")
	print "                    ", _("Useful for testing during development")
	print "--start-map <map> - ", _("Starts <map>. <map> is the filename of the map, without '.sqlite'")
	print "--load-map <save> - ", _("Loads a saved game. Specify the savegamename.")
	print "--fife-path <path> - ", _("Specify the path to FIFE root directory.")
	print ""
	print _("Debugging options:")
	print "--debug-module <module> -", _("Enable logging for a certain logging module.")
	print ""
	print _("Have fun playing, and if you do, help us developing!")


def find_uh_position():
	"""Returns path, where uh is located"""
	first_guess = os.path.split( os.path.realpath( sys.argv[0]) )[0]
	if os.path.exists('%s/content' % first_guess):
		return first_guess
	else:
		positions = ['/usr/share/games',
			     '/usr/share',
			     '/usr/local/share/games',
			     '/usr/local/share',
			     ]

		for i in positions:
			if os.path.exists('%s/unknown-horizons' % i):
				return '%s/unknown-horizons' % i


if __name__ == '__main__':


	#chdir to Unknown Horizons root
	os.chdir( find_uh_position() )
	logging.config.fileConfig('content/logging.conf')
	gettext.install("unknownhorizons", "po", unicode=1)

	# parse arguments
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hd", \
						   ["help", "debug", "fife-in-library-path", "start-dev-map", \
							    "start-map=", "enable-unstable-features", "debug-module=", \
									"load-map=", "fife-path=", "profile"])
	except getopt.GetoptError, err:
		print str(err)
		print_help()
		exit(1)

	fife_in_library_path = False
	fife_custom_path = None

	command_line_arguments = { \
		         "start_dev_map": False, \
					   "start_map": None, \
						 "load_map": None,
					   "unstable_features": False, \
					   "debug": False, \
						 "profile": False}

	# apply arguments
	for o, a in opts:
		if o in ("-h", "--help"):
			print_help()
			exit(1)
		elif o in ("-d", "--debug"):
			logging.getLogger().setLevel(logging.DEBUG)
			command_line_arguments['debug'] = True
			# init the logfile handler with a dynamic filename
			logfilename = "unkown-horizons-"+time.strftime("%y-%m-%d_%H-%M-%S")+".log"
			file_handler = logging.FileHandler(logfilename, 'w')
			logging.getLogger().addHandler(file_handler)
		elif o == "--fife-in-library-path":
			# this is currently only for internal use, therefore not in the help message
			fife_in_library_path = True
		elif o == "--start-dev-map":
			# automatically starts development map
			command_line_arguments['start_dev_map'] = True
		elif o == "--start-map":
			# start map selected by commandline arg
			command_line_arguments['start_map'] = a
		elif o == "--load-map":
			# load map selected by commandline arg
			command_line_arguments['load_map'] = a
		elif o == "--enable-unstable-features":
			command_line_arguments["unstable_features"] = True
		elif o == "--debug-module":
			# enable logging for this module
			logging.getLogger(a).setLevel(logging.DEBUG)
		elif o == "--fife-path":
			# specify custom path to FIFE engine
			fife_custom_path = a
		elif o == "--profile":
			command_line_arguments['profile'] = True

	#find fife and setup search paths, if it can't be imported yet
	try:
		import fife
	except ImportError, e:
		if fife_in_library_path:
			# fife should already be in LD_LIBRARY_PATH
			print 'Failed to load fife:', e
			exit(1)
		log().debug('Searching for FIFE')
		find_FIFE(fife_custom_path)

	#print _("Launching Unknown Horizons")

	#for some external libraries distributed with unknownhorizons
	sys.path.append('horizons/ext')

	#start unknownhorizons
	import horizons.main
	if not command_line_arguments['profile']:
		horizons.main.start(command_line_arguments)
	else:
		import profile
		import tempfile
		outfilename = tempfile.mkstemp(text = True)[1]
		log().warning('Starting profile mode. Writing output to: %s', outfilename)
		profile.runctx('horizons.main.start(command_line_arguments)', globals(), locals(), \
									 outfilename)
		log().warning('Program ended. Profiling output: %s', outfilename)

