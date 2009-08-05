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
	start_uh_group.add_option("--start-map", dest="start_map", metavar="<map>", \
														help=_("Starts <map>. <map> is the mapname (filename without extension)"))
	start_uh_group.add_option("--start-dev-map", dest="start_dev_map", action="store_true", \
			default=False, help=_("Starts the development map without displaying the main menu."))
	start_uh_group.add_option("--load-map", dest="load_map", metavar="<save>", \
														help=_("Loads a saved game. <save> is the savegamename."))
	start_uh_group.add_option("--load-last-quicksave", dest="load_quicksave", action="store_true", \
														help=_("Loads the last quicksave."))
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


	parser = get_option_parser()
	(options, args) = parser.parse_args()

	# apply options
	if options.debug:
		logging.getLogger().setLevel(logging.DEBUG)
		# init a logfile handler with a dynamic filename
		logfilename = "unknown-horizons-%s.log" % time.strftime("%y-%m-%d_%H-%M-%S")
		print 'Logging to stdout and %s' % logfilename
		file_handler = logging.FileHandler(logfilename, 'w')
		logging.getLogger().addHandler(file_handler)
	for module in options.debug_module:
		logging.getLogger(module).setLevel(logging.DEBUG)

	import environment
	# NOTE: this might cause a program restart
	environment.init()

	# parse options

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

