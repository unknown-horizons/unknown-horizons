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

"""TUTORIAL: Welcome to the Unknown Horizons in-code tutorial!
This is a guide for people who are interested in how the code works.
All parts of it are marked with 'TUTORIAL', and every entry contains
a pointer to the next step. Have fun :-)

This is the Unknown Horizons launcher; it looks for FIFE and tries
to start the game. You usually don't need to work with this directly.
If you want to dig into the game, continue to horizons/main.py. """

__all__ = ['init_environment', 'get_fife_path']

import sys
import os
import os.path
import gettext
import time
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

def show_error_message(title, message):
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

if __name__ == '__main__':
    	# python up to version 2.6.1 returns an int. http://bugs.python.org/issue5561
	if platform.python_version_tuple()[0] not in (2,'2'):
		show_error_message('Unsupported Python version', 'Python 2 is required to run Unknown Horizons.')

def log():
	"""Returns Logger"""
	return logging.getLogger("run_uh")

logfilename = None
logfile = None

def find_uh_position():
	"""Returns path, where uh is located"""
	# first check around cur dir and sys.argv[0]
	for i in (
		os.path.split(sys.argv[0])[0],
		'.', '..'
		):
		i = os.path.realpath(i)
		if os.path.exists(os.path.join(i, 'content')):
			return i
	else:
		# also check system wide dirs
		positions = (
			'/usr/share/games',
			'/usr/share',
			'/usr/local/share/games',
			'/usr/local/share'
		)
		for i in positions:
			pos = os.path.join(i, 'unknown-horizons')
			if os.path.exists(pos):
				return pos
	raise RuntimeError('Cannot find location of Unknown Horizons.')

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
	dev_group.add_option("--fife-in-library-path", dest="fife_in_library_path", action="store_true",
	             default=False, help=optparse.SUPPRESS_HELP)
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
		dev_group.add_option("--interactive-shell", action="store_true", dest="interactive_shell",
	             help="Starts an IPython kernel. Connect to the shell with: ipython console --existing")
		dev_group.add_option("--no-atlas-generation", action="store_false", dest="atlas_generation",
	             default=True, help="Disable atlas generation.")
	p.add_option_group(dev_group)

	return p

def create_user_dirs():
	"""Creates the userdir and subdirs. Includes from horizons."""
	from horizons.constants import PATHS
	for directory in (PATHS.USER_DIR, PATHS.LOG_DIR, PATHS.SCREENSHOT_DIR):
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

def main():
	# abort silently on signal
	signal.signal(signal.SIGINT, functools.partial(exithandler, 130))
	signal.signal(signal.SIGTERM, functools.partial(exithandler, 1))

	# use locale-specific time.strftime handling.
	try:
		locale.setlocale(locale.LC_TIME, '')
	except locale.Error: # Workaround for "locale.Error: unsupported locale setting"
		pass

	#chdir to Unknown Horizons root
	os.chdir(find_uh_position())
	logging.config.fileConfig(os.path.join('content', 'logging.conf'))

	create_user_dirs()

	options = get_option_parser().parse_args()[0]
	setup_debugging(options)

	# NOTE: this might cause a program restart
	init_environment()

	# test if required libs can be found or display specific error message
	try:
		import yaml
	except ImportError:
		headline = _('Error: Unable to find required library "PyYAML".')
		msg = _("PyYAML (a required library) is missing and needs to be installed.") + "\n" + \
		    _('The Windows installer is available at http://pyyaml.org/wiki/PyYAML.') + " " + \
		    _('Linux users should find it using their package manager under the name "pyyaml" or "python-yaml".')
		show_error_message(headline, msg)

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

def check_fife_revision(fife):
	revision = fife.getRevision() if hasattr(fife, 'getRevision') else 0
	version = fife.getVersion() if hasattr(fife, 'getVersion') else 'unknown'

	from horizons.constants import VERSION
	if VERSION.MIN_FIFE_REVISION > revision:
		log().warning('Unsupported fife revision %d (version %s); at least %d required',
		              revision, version, VERSION.MIN_FIFE_REVISION)
	else:
		log().debug('Using fife revision %d (version %s); at least %d required', revision,
		            version, VERSION.MIN_FIFE_REVISION)

"""
Functions controlling the program environment.
NOTE: these are supposed to be in an extra file, but are placed here for simplifying
			distribution
"""
def setup_fife(args):
	""" Find FIFE and setup search paths, if it can't be imported yet."""
	try:
		from fife import fife
	except ImportError as e:
		if '--fife-in-library-path' in args:
			# fife should already be in LD_LIBRARY_PATH
			log_paths()
			err_str = str(e)
			if err_str == 'DLL load failed: %1 is not a valid Win32 application.':
				show_error_message('Unsupported Python version',
				                   '32 bit FIFE requires 32 bit (x86) Python 2.')
			else:
				show_error_message('Failed to load FIFE', err_str)
		log().debug('Failed to load FIFE from default paths: %s', e)
		log().debug('Searching for FIFE')
		find_FIFE() # this restarts or terminates the program
		assert False

	log().debug('Using fife: %s', fife)
	check_fife_revision(fife)

	for arg in ['--fife-in-library-path', '--fife-path']:
		if arg in args:
			args.remove(arg)


def init_environment():
	"""Sets up everything. Use in any program that requires access to FIFE and uh modules.
	It will parse sys.args, so this var has to contain only valid uh options."""

	# install dummy translation
	gettext.install('', unicode=True)

	options = get_option_parser().parse_args()[0]

	if options.fife_path and not options.fife_in_library_path:
		# we got an explicit path, search there
		# (but skip on second run, else we've got an endless loop)
		find_FIFE(options.fife_path)

	# find FIFE and setup search paths, if it can't be imported yet
	setup_fife(sys.argv)


def get_fife_path(fife_custom_path=None):
	"""Returns absolute path to FIFE engine. Calls sys.exit() if it can't be found."""
	# assemble a list of paths where FIFE could be located at
	_paths = []
	# check if there is a config file (has to be called config.py)

	# first check for commandline arg
	if fife_custom_path is not None:
		_paths.append(fife_custom_path)
		if not check_path_for_fife(fife_custom_path):
			print('Specified invalid FIFE path: %s' % fife_custom_path)
			exit(1)
	else:
		# no command line parameter, now check for config
		try:
			import config
			_paths.append(config.fife_path)
			if not check_path_for_fife(config.fife_path):
				print('Invalid fife_path in config.py: %s' % config.fife_path)
				exit(1)
		except (ImportError, AttributeError):
		# no config, try frequently used paths
			_paths += [os.path.join(a, b, c) for
			           a in ('.', '..', '../..') for
			           b in ('.', 'fife', 'FIFE', 'Fife') for
			           c in ('.', 'trunk')]

	fife_path = None
	for p in _paths:
		if p not in sys.path: # skip dirs where import would have found FIFE
			p = os.path.abspath(p)
			log().debug("Searching for FIFE in %s", p)
			if check_path_for_fife(p):
				fife_path = p

				log().debug("Found FIFE in %s", fife_path)

				# add python paths (<fife>/engine/extensions <fife>/engine/swigwrappers/python)
				pythonpaths = [os.path.join(fife_path, 'engine', 'python')]
				for path in pythonpaths:
					if os.path.exists(path):
						sys.path.append(path)
					if 'PYTHONPATH' in os.environ:
						os.environ['PYTHONPATH'] += os.path.pathsep + path
					else:
						os.environ['PYTHONPATH'] = path

				# add windows paths (<fife>/.)
				if 'PATH' in os.environ:
					os.environ['PATH'] += os.path.pathsep + fife_path
				else:
					os.environ['PATH'] = fife_path
				os.path.defpath += os.path.pathsep + fife_path
				break
	else:
		print(_('FIFE was not found.'))
		sys.exit(1)
	return fife_path

def check_path_for_fife(path):
	"""Checks if typical FIFE directories exist in path. This does not guarantee, that it's
	really a FIFE dir, but it generally works."""
	absolute_path = os.path.abspath(path)
	for pe in [os.path.join(absolute_path, a) for a in ('.', 'engine', 'engine/python/fife',
		                                               'engine/python/fife/extensions')]:
		if not os.path.exists(pe):
			return False
	return True

def find_FIFE(fife_custom_path=None):
	"""Inserts path to FIFE engine to $LD_LIBRARY_PATH (environment variable).
	If it's already there, the function will return, else
	it will restart uh with correct $LD_LIBRARY_PATH. """
	global logfilename
	fife_path = get_fife_path(fife_custom_path) # terminates program if FIFE can't be found

	os.environ['LD_LIBRARY_PATH'] = os.path.pathsep.join( \
		[ os.path.abspath(fife_path + '/' + a) for  \
			a in ('ext/minizip', 'ext/install/lib') ] + \
		(os.environ['LD_LIBRARY_PATH'].split(os.path.pathsep) if \
		 os.environ.has_key('LD_LIBRARY_PATH') else []))

	log().debug("Restarting with proper LD_LIBRARY_PATH...")
	log_paths()

	# assemble args (python run_uh.py ..)
	args = [sys.executable] + sys.argv + ["--fife-in-library-path"]

	# WORKAROUND: windows systems don't handle spaces in arguments for execvp correctly.
	if platform.system() != 'Windows':
		if logfilename:
			args += ["--logfile", logfilename]
		log().debug("Restarting with args %s", args)
		os.execvp(args[0], args)
	else:
		args[1] = '"%s"' % args[1]
		args += ["--logfile", '"%s"' % logfilename]
		log().debug("Restarting using windows workaround with args %s", args)
		os.system(" ".join(args))
		sys.exit(0)

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
