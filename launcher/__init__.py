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

import functools
import multiprocessing
import signal
import sys
import time

from launcher.optionsmanager import OptionsManager
from launcher.commandlinegamemanager import StartGameFromCommandLineEvent
from launcher.menumanager import OpenMainMenuEvent
from launcher.gameconfiguration import GameConfiguration

class Launcher(object):
	def __init__(self):
		super(Launcher, self).__init__()
		self.options = OptionsManager()
		self.menu = None
		self.game = None
		self.events = multiprocessing.Queue()

	def terminate(self, exitcode):
		"""Kill everything."""
		if self.menu:
			self.menu.terminate()
		if self.game:
			self.game.terminate()
		sys.exit(exitcode)

	def _exithandler(self, exitcode, signum, frame):
		"""Quietly handle a kill signal."""
		# restore default signal handlers
		signal.signal(signal.SIGINT, signal.SIG_IGN)
		signal.signal(signal.SIGTERM, signal.SIG_IGN)

		print('')
		print('Oh my god! They killed UH.')
		print('You bastards!')
		self.terminate(exitcode)

	def _check_children_running(self):
		"""Check that the child processes are still correctly working."""
		if self.menu:
			if not self.menu.is_alive():
				print 'the menu has crashed'
				self.terminate(1)
		if self.game:
			if not self.game.is_alive():
				print 'the game has crashed'
				self.terminate(1)

	def _setup_signal_handling(self):
		# abort silently on signal
		signal.signal(signal.SIGINT, functools.partial(self._exithandler, 130))
		signal.signal(signal.SIGTERM, functools.partial(self._exithandler, 1))

	def run(self):
		self._setup_signal_handling()

		if self.options.opening_menu():
			self.events.put_nowait(OpenMainMenuEvent())
		else:
			self.events.put_nowait(StartGameFromCommandLineEvent())
		self.loop()

	def loop(self):
		while True:
			self._check_children_running()
			if self.events.empty():
				time.sleep(0.001)
			else:
				event = self.events.get()
				event.execute(self)

	def _close_process(self, name):
		process = getattr(self, name)
		if process:
			# the reference is set to None before killing the process because this makes
			# it easy to detect whether the process has crashed.
			setattr(self, name, None)
			process.terminate()

	def close_menu(self):
		self._close_process('menu')

	def close_game(self):
		self._close_process('game')
		self.options.clear_startup_options()

	def quit_session(self):
		assert self.game
		self.close_game()
		self.events.put_nowait(OpenMainMenuEvent())
