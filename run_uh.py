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
import locale
import logging
import logging.config
import logging.handlers
import traceback
import platform

from launcher.dependencycheck import show_error_message

# NOTE: do NOT import anything from horizons.* into global scope
# this will break any run_uh imports from other locations (e.g. _get_version())

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
		if os.path.exists( os.path.join(i, 'content')):
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
			if os.path.exists( pos ):
				return pos
	raise RuntimeError('Cannot find location of Unknown Horizons.')

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
		print(_('We are very sorry for this and want to fix underlying error.'))
		print(_('In order to do this, we need the information from the logfile:'))
		print(outfilename)
		print(_('Please give it to us via IRC or our forum, for both see http://unknown-horizons.org .'))
	return excepthook

def main(options):
	# use locale-specific time.strftime handling.
	try:
		locale.setlocale(locale.LC_TIME, '')
	except locale.Error: # Workaround for "locale.Error: unsupported locale setting"
		pass

	#chdir to Unknown Horizons root
	os.chdir( find_uh_position() )
	logging.config.fileConfig( os.path.join('content', 'logging.conf'))

	create_user_dirs()

	setup_debugging(options)

	# NOTE: this might cause a program restart
	init_environment(options)

	# test if required libs can be found or display specific error message
	try:
		import yaml
	except ImportError:
		headline = _('Error: Unable to find required library "PyYAML".')
		msg = _("We are sorry to inform you that a library that is required by Unknown Horizons, is missing and needs to be installed.") + "\n" + \
		    _('Installers for Windows users are available at "http://pyyaml.org/wiki/PyYAML", Linux users should find it in their packagement management system under the name "pyyaml" or "python-yaml".')
		show_error_message(headline, msg)

	"""
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

		outfilename = os.path.join(profiling_dir, time.strftime('%Y-%m-%d_%H-%M-%S') + '.prof')
		print('Starting in profile mode. Writing output to: %s' % outfilename)
		profile.runctx('horizons.main.start(options)', globals(), locals(), outfilename)
		print('Program ended. Profiling output: %s' % outfilename)
	"""

	if logfile:
		logfile.close()
	#if ret:
	#	print(_('Thank you for using Unknown Horizons!'))


def setup_debugging(options):
	"""Parses and applies options
	@param options: parameters: debug, debug_module, debug_log_only, logfile
	"""
	global logfilename, logfile

	# not too nice way of sharing code, but it is necessary because code from this file
	# can't be accessed elsewhere on every distribution, and we can't just access other code.
	# however, passing options is guaranteed to work
	options.setup_debugging_func = setup_debugging

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
		print('Logging to %s' % logfilename.encode('utf-8', 'replace'))
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
			logging.getLogger().addHandler( logging.StreamHandler(sys.stderr) )

		log_sys_info()


"""
Functions controlling the program environment.
NOTE: these are supposed to be in an extra file, but are placed here for simplifying
			distribution
"""
def setup_fife(options):
	""" Find FIFE and setup search paths, if it can't be imported yet."""
	try:
		from fife import fife
	except ImportError as e:
		if options.fife_in_library_path:
			# fife should already be in LD_LIBRARY_PATH
			log_paths()
			err_str = str(e)
			if err_str == 'DLL load failed: %1 is not a valid Win32 application.':
				show_error_message('Unsupported Python version', '32 bit FIFE requires 32 bit (x86) Python 2.')
			else:
				show_error_message('Failed to load FIFE', err_str)
		log().debug('Failed to load FIFE from default paths: %s', e)
		log().debug('Searching for FIFE')
		find_FIFE() # this restarts or terminates the program
		assert False

	log().debug('Using fife: %s', fife)


def init_environment(options):
	"""Sets up everything. Use in any program that requires access to FIFE and uh modules.
	It will parse sys.args, so this var has to contain only valid uh options."""

	# install dummy translation
	gettext.install('', unicode=True)

	if options.fife_path and not options.fife_in_library_path:
		# we got an explicit path, search there
		# (but skip on second run, else we've got an endless loop)
		find_FIFE(options.fife_path)

	# find FIFE and setup search paths, if it can't be imported yet
	setup_fife(options)


def get_fife_path(fife_custom_path=None):
	"""Returns absolute path to FIFE engine. Calls sys.exit() if it can't be found."""
	# assemble a list of paths where FIFE could be located at
	_paths = []
	# check if there is a config file (has to be called config.py)

	# first check for commandline arg
	if fife_custom_path is not None:
		_paths.append(fife_custom_path)
		if not check_path_for_fife(fife_custom_path):
			print('Specified invalid FIFE path: %s' %  fife_custom_path)
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
			_paths += [ os.path.join(a, b, c) for \
									a in ('.', '..', '../..') for \
									b in ('.', 'fife', 'FIFE', 'Fife') for \
									c in ('.', 'trunk') ]

	fife_path = None
	for p in _paths:
		if p not in sys.path: # skip dirs where import would have found FIFE
			p = os.path.abspath(p)
			log().debug("Searching for FIFE in %s", p)
			if check_path_for_fife(p):
				fife_path = p

				log().debug("Found FIFE in %s", fife_path)

				# add python paths (<fife>/engine/extensions <fife>/engine/swigwrappers/python)
				pythonpaths = [ os.path.join( fife_path, 'engine/python') ]
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
	for pe in [ os.path.join(absolute_path, a) for a in ('.', 'engine', 'engine/python/fife',  \
				                                               'engine/python/fife/extensions') ]:
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
	args = [sys.executable] + sys.argv + [ "--fife-in-library-path" ]

	# WORKAROUND: windows systems don't handle spaces in arguments for execvp correctly.
	if platform.system() != 'Windows':
		if logfilename:
			args += [ "--logfile", logfilename ]
		log().debug("Restarting with args %s", args)
		os.execvp(args[0], args)
	else:
		args[1] = '"%s"' % args[1]
		args += [ "--logfile", '"%s"' % logfilename ]
		log().debug("Restarting using windows workaround with args %s", args)
		os.system(" ".join(args))
		sys.exit(0)

def log_paths():
	"""Prints debug info about paths to log"""
	log().debug("SYS.PATH: %s", sys.path)
	log().debug('PATHSEP: "%s" SEP: "%s"', os.path.pathsep, os.path.sep)
	log().debug("LD_LIBRARY_PATH: %s", os.environ['LD_LIBRARY_PATH'])
	log().debug("PATH: %s", os.environ['PATH'])
	log().debug("PYTHONPATH %s", os.environ.get('PYTHONPATH', '<undefined>'))

def log_sys_info():
	"""Prints debug info about the current system to log"""
	log().debug("Python version: %s", sys.version_info)
	log().debug("Platform: %s", platform.platform())
