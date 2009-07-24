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
import optparse

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

def get_option_parser():
	"""Returns inited OptionParser object"""
	p = optparse.OptionParser()
	p.add_option("-d", "--debug", dest="debug", action="store_true", default=False, \
							 help=_("Enable debug output"))
	p.add_option("--fife-path", dest="fife_path", metavar="<path>", \
							 help=_("Specify the path to FIFE root directory."))

	start_uh_group = optparse.OptionGroup(p, _("Starting unknown horizons"))
	start_uh_group.add_option("--start-dev-map", dest="start_dev_map", action="store_true", \
			default=False, help=_("Starts the development map without displaying the main menu."))
	start_uh_group.add_option("--start-map", dest="start_map", metavar="<map>", \
														help=_("Starts <map>. <map> is the mapname (filename without extension)"))
	start_uh_group.add_option("--load-map", dest="load_map", metavar="<save>", \
														help=_("Loads a saved game. <save> is the savegamename."))
	p.add_option_group(start_uh_group)

	dev_group = optparse.OptionGroup(p, _("Development options"))
	dev_group.add_option("--debug-module", action="append", dest="debug_module", \
											 metavar="<module>", default=[], \
											 help=_("Enable logging for a certain logging module."))
	dev_group.add_option("--fife-in-library-path", dest="fife_in_library_path", \
											 action="store_true", default=False, help=_("For internal use only."))
	dev_group.add_option("--enable-unstable-features", dest="unstable_features", \
											 action="store_true", default=False, help=_("Enables unstable features"))
	dev_group.add_option("--profile", dest="profile", action="store_true", default=False, \
											 help=_("Enable profiling"))
	p.add_option_group(dev_group)

	return p


if __name__ == '__main__':

	#chdir to Unknown Horizons root
	os.chdir( find_uh_position() )
	logging.config.fileConfig('content/logging.conf')
	gettext.install("unknownhorizons", "po", unicode=1)

	# parse options
	parser = get_option_parser()
	(options, args) = parser.parse_args()

	# apply options
	if options.debug:
		logging.getLogger().setLevel(logging.DEBUG)
		# init the logfile handler with a dynamic filename
		logfilename = "unknown-horizons-%s.log" % time.strftime("%y-%m-%d_%H-%M-%S")
		file_handler = logging.FileHandler(logfilename, 'w')
		logging.getLogger().addHandler(file_handler)
	for module in options.debug_module:
		logging.getLogger(module).setLevel(logging.DEBUG)


	#find fife and setup search paths, if it can't be imported yet
	try:
		import fife
	except ImportError, e:
		if options.fife_in_library_path:
			# fife should already be in LD_LIBRARY_PATH
			print 'Failed to load fife:', e
			exit(1)
		log().debug('Searching for FIFE')
		find_FIFE(options.fife_path)

	#print _("Launching Unknown Horizons")

	#for some external libraries distributed with unknownhorizons
	sys.path.append('horizons/ext')

	#start unknownhorizons
	import horizons.main
	if not options.profile:
		# start normal
		horizons.main.start(options)
	else:
		# start with profiling
		import profile
		import tempfile
		outfilename = tempfile.mkstemp(text = True)[1]
		log().warning('Starting profile mode. Writing output to: %s', outfilename)
		profile.runctx('horizons.main.start(options)', globals(), locals(), \
									 outfilename)
		log().warning('Program ended. Profiling output: %s', outfilename)

