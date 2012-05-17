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

from fife import fife
import code
import sys
import datetime
import string
import os.path

import horizons.main

from horizons.gui.keylisteners import KeyConfig
from horizons.util.living import LivingObject
from horizons.constants import PATHS

class MainListener(fife.IKeyListener, fife.ConsoleExecuter, LivingObject):
	"""MainListener Class to process events of main window"""

	def __init__(self, gui):
		super(MainListener, self).__init__()
		sys.displayhook = self # see __call__ for detailed info
		self.gui = gui
		fife.IKeyListener.__init__(self)
		fife.ConsoleExecuter.__init__(self)
		horizons.main.fife.eventmanager.addKeyListener(self)
		horizons.main.fife.console.setConsoleExecuter(self)

		#ugly but works o_O
		class CmdListener(fife.ICommandListener): pass
		self.cmdlist = CmdListener()
		horizons.main.fife.eventmanager.addCommandListener(self.cmdlist)
		self.cmdlist.onCommand = self.onCommand

		self.commandbuffer = ''

	def __call__(self, cmd):
		"""
		The default displayhook method would save computation results
		in a temp variable called _.  This is rather unfortunate because
		our gettext functionality also is globally imported under that name.
		To solve, we have to set a custom Executer not storing anything in _.
		Cf. FIFE ticket: http://fife.trac.cvsdude.com/engine/ticket/560

		Right now does nothing besides printing to interactive and user shell.
		#TODO Feel free to implement ;-)
		"""
		print "calling %s" % cmd

	def end(self):
		horizons.main.fife.eventmanager.removeKeyListener(self)
		super(MainListener, self).end()

	def keyPressed(self, evt):
		if evt.isConsumed():
			return

		action = KeyConfig().translate(evt)
		_Actions = KeyConfig._Actions

		key_event_handled = True

		if action == _Actions.ESCAPE:
			self.gui.on_escape()
		elif action == _Actions.CONSOLE:
			horizons.main.fife.console.toggleShowHide()
		elif action == _Actions.HELP:
			self.gui.on_help()
		elif action == _Actions.SCREENSHOT:
			screenshotfilename = os.path.join(PATHS.SCREENSHOT_DIR,
			            string.replace(datetime.datetime.now().isoformat('.') + ".png", ":", "-"))

			''' the filename is changed into a string, cause it looks like FIFE can't handle unicode strings yet
			it's only a workaround to prevent a crash ...
			this should be changed later to unicode(string.replace(datetime... '''

			screenshotfilename = str(screenshotfilename)
			horizons.main.fife.engine.getRenderBackend().captureScreen(screenshotfilename)
			if self.gui.session is not None:
				# ingame message if there is a session
				self.gui.session.ingame_gui.message_widget.add(None, None, 'SCREENSHOT', \
																													{'file': screenshotfilename})
		elif action == _Actions.QUICKLOAD:
			from horizons.main import _load_last_quicksave
			_load_last_quicksave(self.gui.session)
		else:
			key_event_handled = False # nope, nothing triggered

		if key_event_handled:
			evt.consume() # prevent other listeners from being called



	def keyReleased(self, evt):
		pass

	def onCommand(self, command):
		if command.getCommandType() == fife.CMD_QUIT_GAME:
			horizons.main.quit()
			command.consume()

	def onConsoleCommand(self, command):
		if command == ' ':
			command = ''
		try:
			cmd = code.compile_command(self.commandbuffer + "\n" + command)
		except BaseException as e:
			self.commandbuffer = ''
			return str(e)
		if cmd is None:
			self.commandbuffer += "\n" + command
			return ''
		self.commandbuffer = ''
		oldout = sys.stdout
		class console_file(object):
			def __init__(self, copy=None):
				self.buffer = ''
				self.copy = copy
			def write(self, string):
				parts = (self.buffer + string).split("\n")
				self.buffer = parts.pop()
				for p in parts:
					horizons.main.fife.console.println(p)
				self.copy.write(string)
			def __del__(self):
				if len(self.buffer) > 0:
					self.write('\n')
		sys.stdout = console_file(oldout)
		try:
			exec cmd in globals()
		except BaseException as e:
			sys.stdout = oldout
			return str(e)
		sys.stdout = oldout
		return ''

	def onToolsClick(self):
		"""
		Define what happens if we click on the Tools button in FIFE console
		"""
		self.onConsoleCommand('import debug')
