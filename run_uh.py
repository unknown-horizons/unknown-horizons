#!/usr/bin/env python

# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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

"""TUTORIAL: Welcome to the Unknown Horizons in-code tutorial!
This is a guide for people who are interested in how the code works.
All parts of it are marked with 'TUTORIAL', and every entry contains
a pointer to the next step. Have fun :-)

This is the Unknown Horizons launcher; it looks for FIFE and tries
to start the game. You usually don't need to work with this directly.
If you want to dig into the game, continue to horizons/main.py. """

__all__ = ['init_environment']

import sys
import os
import os.path
import gettext
import time
import imp
import functools
import locale
import logging
import logging.config
import logging.handlers
import optparse
import signal
import traceback
import platform

# NOTE: do NOT import anything from horizons.* into global scope
# this will break any run_uh imports from other locations (e.g. _get_version())

def exit_with_error(title, message):
	if title + '.' != message:
		print(title)
	print(message)

	try:
		import Tkinter
		import tkMessageBox
		window = Tkinter.Tk()
		window.wm_withdraw()
		tkMessageBox.showerror(title, message)
	except:
		# tkinter may be missing
		pass
	exit(1)

def check_python_version():
	# python up to version 2.6.1 returns an int. http://bugs.python.org/issue5561
	if platform.python_version_tuple()[0] not in (2,'2'):
		exit_with_error('Unsupported Python version', 'Python 2 is required to run Unknown Horizons.')


check_python_version()


def log():
	"""Returns Logger"""
	return logging.getLogger("run_uh")

logfilename = None
logfile = None

def get_option_parser():
	"""Returns inited OptionParser object"""
	from horizons.constants import VERSION
	p = optparse.OptionParser(usage="%prog [options]", version=VERSION.string())
	p.add_option("-d", "--debug", dest="debug", action="store_true",
	             default=False, help="Enable debug output to stderr and a logfile.")
	p.add_option("--fife-path", dest="fife_path", metavar="<path>",
	             help="Specify the path to FIFE root directory.")
	p.add_option("--restore-settings", dest="restore_settings", action="store_true", default=False,
	             help="Restores the default settings. "
	                  "Useful if Unknown Horizons crashes on startup due to misconfiguration.")
	p.add_option("--mp-master", dest="mp_master", metavar="<ip:port>",
	             help="Specify alternative multiplayer master server.")
	p.add_option("--mp-bind", dest="mp_bind", metavar="<ip:port>",
	             help="Specify network address to bind local network client to. "
	                  "This is useful if NAT holepunching is not working but you can forward a static port.")


	start_uh = optparse.OptionGroup(p, "Starting Unknown Horizons")
	start_uh.add_option("--start-map", dest="start_map", metavar="<map>",
	             help="Starts <map>. <map> is the mapname.")
	start_uh.add_option("--start-random-map", dest="start_random_map", action="store_true",
	             help="Starts a random map.")
	start_uh.add_option("--start-specific-random-map", dest="start_specific_random_map",
	             metavar="<seed>", help="Starts a random map with seed <seed>.")
	start_uh.add_option("--start-scenario", dest="start_scenario", metavar="<scenario>",
	             help="Starts <scenario>. <scenario> is the scenarioname.")
	start_uh.add_option("--start-dev-map", dest="start_dev_map", action="store_true",
	             default=False, help="Starts the development map without displaying the main menu.")
	start_uh.add_option("--load-game", dest="load_game", metavar="<game>",
	             help="Loads a saved game. <game> is the saved game's name.")
	start_uh.add_option("--load-last-quicksave", dest="load_quicksave", action="store_true",
	             help="Loads the last quicksave.")
	start_uh.add_option("--edit-map", dest="edit_map", metavar="<map>",
	             help="Edit map <map>.")
	start_uh.add_option("--edit-game-map", dest="edit_game_map", metavar="<game>",
	             help="Edit the map from the saved game <game>.")
	p.add_option_group(start_uh)

	ai_group = optparse.OptionGroup(p, "AI options")
	ai_group.add_option("--ai-players", dest="ai_players", metavar="<ai_players>",
	             type="int", default=0,
	             help="Uses <ai_players> AI players (excludes the possible human-AI hybrid; defaults to 0).")
	ai_group.add_option("--human-ai-hybrid", dest="human_ai", action="store_true",
	             help="Makes the human player a human-AI hybrid (for development only).")
	ai_group.add_option("--force-player-id", dest="force_player_id",
	             metavar="<force_player_id>", type="int", default=None,
	             help="Set the player with id <force_player_id> as the active (human) player.")
	ai_group.add_option("--ai-highlights", dest="ai_highlights", action="store_true",
	             help="Shows AI plans as highlights (for development only).")
	ai_group.add_option("--ai-combat-highlights", dest="ai_combat_highlights", action="store_true",
	             help="Highlights combat ranges for units controlled by AI Players (for development only).")
	p.add_option_group(ai_group)

	dev_group = optparse.OptionGroup(p, "Development options")
	dev_group.add_option("--debug-log-only", dest="debug_log_only", action="store_true",
	             default=False, help="Write debug output only to logfile, not to console. Implies -d.")
	dev_group.add_option("--debug-module", action="append", dest="debug_module",
	             metavar="<module>", default=[],
	             help="Enable logging for a certain logging module (for developing only).")
	dev_group.add_option("--logfile", dest="logfile", metavar="<filename>",
	             help="Writes log to <filename> instead of to the uh-userdir")
	dev_group.add_option("--profile", dest="profile", action="store_true",
	             default=False, help="Enable profiling (for developing only).")
	dev_group.add_option("--max-ticks", dest="max_ticks", metavar="<max_ticks>", type="int",
	             help="Run the game for <max_ticks> ticks.")
	dev_group.add_option("--no-freeze-protection", dest="freeze_protection", action="store_false",
	             default=True, help="Disable freeze protection.")
	dev_group.add_option("--string-previewer", dest="stringpreview", action="store_true",
	             default=False, help="Enable the string previewer tool for scenario writers")
	dev_group.add_option("--no-preload", dest="nopreload", action="store_true",
	             default=False, help="Disable preloading while in main menu")
	dev_group.add_option("--game-speed", dest="gamespeed", metavar="<game_speed>", type="float",
	             help="Run the game in the given speed (Values: 0.5, 1, 2, 3, 4, 6, 8, 11, 20)")
	dev_group.add_option("--gui-test", dest="gui_test", metavar="<test>",
	             default=False, help=optparse.SUPPRESS_HELP)
	dev_group.add_option("--gui-log", dest="log_gui", action="store_true",
	             default=False, help="Log gui interactions")
	dev_group.add_option("--sp-seed", dest="sp_seed", metavar="<seed>", type="int",
	             help="Use this seed for singleplayer sessions.")
	dev_group.add_option("--generate-minimap", dest="generate_minimap",
	             metavar="<parameters>", help=optparse.SUPPRESS_HELP)
	dev_group.add_option("--create-mp-game", action="store_true", dest="create_mp_game",
	             help="Create an multiplayer game with default settings.")
	dev_group.add_option("--join-mp-game", action="store_true", dest="join_mp_game",
	             help="Join first multiplayer game.")
	if VERSION.IS_DEV_VERSION:
		dev_group.add_option("--no-atlas-generation", action="store_false", dest="atlas_generation",
	             help="Disable atlas generation.")
	# Add dummy default variables for the DEV_VERSION groups above when in release mode
	p.set_defaults(atlas_generation=True)
	p.add_option_group(dev_group)

	return p

def get_content_dir_parent_path():
	"""
	Return the path to the parent of the content dir.
	
	This is usually just the dir the run_uh.py is in but on some Linux installation
	scenarios the horizons dir, the content dir, and run_uh.py are all in different
	locations.
	"""

	options = []
	# Try the directory this file is in. This should work in most cases.
	options.append(os.path.dirname(os.path.realpath(unicode(__file__))))
	# Try often-used paths on Linux.
	for path in ('/usr/share/games', '/usr/share', '/usr/local/share/games', '/usr/local/share'):
		options.append(os.path.join(path, u'unknown-horizons'))

	for path in options:
		content_path = os.path.join(path, u'content')
		if os.path.exists(content_path):
			return path
	raise RuntimeError('Unable to find the path to the Unknown Horizons content dir.')

def create_user_dirs():
	"""Creates the userdir and subdirs. Includes from horizons."""
	from horizons.constants import PATHS
	for directory in (PATHS.USER_DIR, PATHS.LOG_DIR, PATHS.USER_MAPS_DIR, PATHS.SCREENSHOT_DIR):
		if not os.path.isdir(directory):
			os.makedirs(directory)

def excepthook_creator(outfilename):
	"""Returns an excepthook function to replace sys.excepthook.
	The returned function does the same as the default, except it also prints the traceback
	to a file.
	@param outfilename: a filename to append traceback to"""
	def excepthook(exception_type, value, tb):
		f = open(outfilename, 'a')
		traceback.print_exception(exception_type, value, tb, file=f)
		traceback.print_exception(exception_type, value, tb)
		print('')
		print(_('Unknown Horizons has crashed.'))
		print('')
		print(_('We are very sorry for this and want to fix the underlying error.'))
		print(_('In order to do this, we need the information from the logfile:'))
		print(outfilename)
		print(_('Please give it to us via IRC or our forum, for both see http://unknown-horizons.org .'))
	return excepthook

def exithandler(exitcode, signum, frame):
	"""Handles a kill quietly"""
	signal.signal(signal.SIGINT, signal.SIG_IGN)
	signal.signal(signal.SIGTERM, signal.SIG_IGN)
	print('')
	print('Oh my god! They killed UH.')
	print('You bastards!')
	if logfile:
		logfile.close()
	sys.exit(exitcode)

def setup_streams():
	"""Ignore output to stderr and stdout if writing to them is not possible."""
	if sys.__stderr__.fileno() < 0:
		sys.stderr = open(os.devnull, 'w')
	if sys.__stdout__.fileno() < 0:
		sys.stdout = open(os.devnull, 'w')

def main():
	# abort silently on signal
	signal.signal(signal.SIGINT, functools.partial(exithandler, 130))
	signal.signal(signal.SIGTERM, functools.partial(exithandler, 1))

	# avoid crashing when writing to unavailable standard streams
	setup_streams()

	# use locale-specific time.strftime handling.
	try:
		locale.setlocale(locale.LC_TIME, '')
	except locale.Error: # Workaround for "locale.Error: unsupported locale setting"
		pass

	# Change the working directory to the parent of the content directory.
	os.chdir(get_content_dir_parent_path())
	logging.config.fileConfig(os.path.join('content', 'logging.conf'))
	create_user_dirs()

	options = get_option_parser().parse_args()[0]
	setup_debugging(options)
	init_environment(True)

	# test if required libs can be found or display specific error message
	try:
		import yaml
	except ImportError:
		headline = _('Error: Unable to find required library "PyYAML".')
		msg = _("PyYAML (a required library) is missing and needs to be installed.") + "\n" + \
		    _('The Windows installer is available at http://pyyaml.org/wiki/PyYAML.') + " " + \
		    _('Linux users should find it using their package manager under the name "pyyaml" or "python-yaml".')
		exit_with_error(headline, msg)

	#start UH
	import horizons.main
	ret = True
	if not options.profile:
		# start normal
		ret = horizons.main.start(options)
	else:
		# start with profiling
		try:
			import cProfile as profile
		except ImportError:
			import profile

		from horizons.constants import PATHS
		profiling_dir = os.path.join(PATHS.USER_DIR, 'profiling')
		if not os.path.exists(profiling_dir):
			os.makedirs(profiling_dir)

		pattern = os.path.join(profiling_dir, time.strftime('%Y-%m-%d') + '.%02d.prof')
		num = 1
		while os.path.exists(pattern % num):
			num += 1

		outfilename = pattern % num
		print('Starting in profile mode. Writing output to: %s' % outfilename)
		profile.runctx('horizons.main.start(options)', globals(), locals(), outfilename)
		print('Program ended. Profiling output: %s' % outfilename)

	if logfile:
		logfile.close()
	if ret:
		print(_('Thank you for using Unknown Horizons!'))


def setup_debugging(options):
	"""Parses and applies options
	@param options: parameters: debug, debug_module, debug_log_only, logfile
	"""
	global logfilename, logfile

	# not too nice way of sharing code, but it is necessary because code from this file
	# can't be accessed elsewhere on every distribution, and we can't just access other code.
	# however, passing options is guaranteed to work
	options.setup_debugging = setup_debugging

	# apply options
	if options.debug or options.debug_log_only:
		logging.getLogger().setLevel(logging.DEBUG)
	for module in options.debug_module:
		if not module in logging.Logger.manager.loggerDict:
			print('No such logger: %s' % module)
			sys.exit(1)
		logging.getLogger(module).setLevel(logging.DEBUG)
	if options.debug or options.debug_module or options.debug_log_only:
		options.debug = True
		# also log to file
		# init a logfile handler with a dynamic filename
		from horizons.constants import PATHS
		if options.logfile:
			logfilename = options.logfile
		else:
			logfilename = os.path.join(PATHS.LOG_DIR, "unknown-horizons-%s.log" %
			                           time.strftime("%Y-%m-%d_%H-%M-%S"))
		print('Logging to {uh} and {fife}'.format(
			uh=logfilename.encode('utf-8', 'replace'),
			fife=os.path.join(os.getcwd(), 'fife.log')) )
		# create logfile
		logfile = open(logfilename, 'w')
		# log there
		file_handler = logging.FileHandler(logfilename, 'a')
		logging.getLogger().addHandler(file_handler)
		# log exceptions
		sys.excepthook = excepthook_creator(logfilename)
		# log any other stdout output there (this happens, when FIFE c++ code launches some
		# FIFE python code and an exception happens there). The exceptionhook only gets
		# a director exception, but no real error message then.
		class StdOutDuplicator(object):
			def write(self, line):
				line = unicode(line)
				sys.__stdout__.write(line)
				logfile.write(line.encode('UTF-8'))
			def flush(self):
				sys.__stdout__.flush()
				logfile.flush()
		sys.stdout = StdOutDuplicator()

		# add a handler to stderr too _but_ only if logfile isn't already a tty
		# this allows --debug-module=<module> --logfile=/dev/stdout
		# without getting logs twice + without enabling debug log for everything
		# (see first if-clause inside that method)
		if not options.debug_log_only and not logfile.isatty():
			logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))

		log_sys_info()

def import_fife(paths):
	try:
		# If FIFE can't be found then this call will throw an exception.
		settings = imp.find_module('fife', paths)
		fife = imp.load_module('fife', *settings)
		try:
			from fife import fife
		except ImportError as e:
			if str(e) != 'cannot import name fife':
				log().warning('Failed to use FIFE from %s', fife)
				log().warning(str(e))
				if str(e) == 'DLL load failed: %1 is not a valid Win32 application.':
					# We found FIFE but the Python and FIFE architectures don't match (Windows).
					exit_with_error('Unsupported Python version', '32 bit FIFE requires 32 bit (x86) Python 2.')
			return False
	except ImportError:
		# FIFE couldn't be found in any of the paths.
		return False
	return True

def find_fife():
	# Use the path the user provided.
	options = get_option_parser().parse_args()[0]
	if options.fife_path:
		fife_path = os.path.abspath(options.fife_path)
		# Support giving the path to FIFE_ROOT/engine/python/fife/__init__.pyc etc.
		if os.path.isfile(fife_path):
			fife_path = os.path.dirname(fife_path)
		# Support giving the path to FIFE_ROOT/engine/python
		if import_fife([fife_path]):
			return True
		# Support giving the path to FIFE_ROOT/engine
		if import_fife([os.path.join(fife_path, 'python')]):
			return True
		# Support giving the path to FIFE_ROOT
		if import_fife([os.path.join(fife_path, 'engine', 'python')]):
			return True
		# Support giving the path to FIFE_ROOT/engine/python/fife
		if import_fife([os.path.join(fife_path, '..')]):
			return True

		# End the search to avoid using the wrong (non-user-specified) FIFE.
		log().error('Unable to find FIFE in %s', fife_path)
		exit(1)

	# Try to use the default FIFE (equivalent of just trying to import it).
	if import_fife(None):
		return True

	# Look for FIFE in the neighborhood of the game dir.
	paths = []
	for opt1 in ('.', '..', '..' + os.sep + '..'):
		for opt2 in ('.', 'fife', 'FIFE', 'Fife', 'fifengine'):
			for opt3 in ('.', 'trunk'):
				path = os.path.abspath(os.path.join('.', opt1, opt2, opt3, 'engine', 'python'))
				if os.path.exists(path):
					paths.append(path)
	return import_fife(paths)

def setup_fife():
	log_paths()
	log_sys_info()
	if not find_fife():
		exit_with_error('Failed to find and/or load FIFE', 'Failed to find and/or load FIFE.')

	from fife import fife
	revision = fife.getRevision() if hasattr(fife, 'getRevision') else 0
	version = fife.getVersion() if hasattr(fife, 'getVersion') else 'unknown'

	from horizons.constants import VERSION
	if VERSION.MIN_FIFE_REVISION > revision:
		log().warning('Unsupported fife revision %d (version %s); at least %d required',
		              revision, version, VERSION.MIN_FIFE_REVISION)
	else:
		log().debug('Using fife revision %d (version %s); at least %d required', revision,
		            version, VERSION.MIN_FIFE_REVISION)

def init_environment(use_fife):
	"""Sets up everything.

	Use in any program that requires access to FIFE and UH modules."""
	# install dummy translation
	gettext.install('', unicode=True)
	if use_fife:
		setup_fife()

def log_paths():
	"""Prints debug info about paths to log"""
	log().debug("SYS.PATH: %s", sys.path)
	log().debug('PATHSEP: "%s" SEP: "%s"', os.path.pathsep, os.path.sep)
	log().debug("LD_LIBRARY_PATH: %s", os.environ.get('LD_LIBRARY_PATH', '<undefined>'))
	log().debug("PATH: %s", os.environ.get('PATH', '<undefined>'))
	log().debug("PYTHONPATH %s", os.environ.get('PYTHONPATH', '<undefined>'))

def log_sys_info():
	"""Prints debug info about the current system to log"""
	log().debug("Python version: %s", sys.version_info)
	log().debug("Platform: %s", platform.platform())

if __name__ == '__main__':
	main()
