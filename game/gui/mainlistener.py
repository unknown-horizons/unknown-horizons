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

import fife
import game.main
import code
import sys
import datetime
import string
from game.util.living import LivingObject

class MainListener(fife.IKeyListener, fife.ConsoleExecuter, LivingObject):
	"""MainListener Class to process events of main window"""

	def __init__(self):
		super(MainListener, self).__init__()
		fife.IKeyListener.__init__(self)
		fife.ConsoleExecuter.__init__(self)
		game.main.fife.eventmanager.addKeyListener(self)
		game.main.fife.console.setConsoleExecuter(self)

		#ugly but works o_O
		class CmdListener(fife.ICommandListener): pass
		self.cmdlist = CmdListener()
		game.main.fife.eventmanager.addCommandListener(self.cmdlist)
		self.cmdlist.onCommand = self.onCommand

		self.commandbuffer = ''

	def end(self):
		game.main.fife.eventmanager.removeKeyListener(self)
		super(MainListener, self).end()

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		keystr = evt.getKey().getAsString().lower()
		if keyval == fife.Key.ESCAPE:
			print "ESCAPE PRESSED"
			game.main.gui.on_escape()
			evt.consume()
		elif keyval == fife.Key.F10:
			game.main.fife.console.toggleShowHide()
			evt.consume()
		elif keyval == fife.Key.F1:
			game.main.gui.on_help()
		elif keystr == 's':
			game.main.fife.engine.getRenderBackend().captureScreen(string.replace("content/screenshots/" + datetime.datetime.now().isoformat('.') + ".png", ":", "-"))

	def keyReleased(self, evt):
		pass

	def onCommand(self, command):
		if command.getCommandType() == fife.CMD_QUIT_GAME:
			game.main.fife.quit()
			command.consume()

	def onConsoleCommand(self, command):
		if command == ' ':
			command = ''
		try:
			cmd = code.compile_command(self.commandbuffer + "\n" + command)
		except BaseException, e:
			self.commandbuffer = ''
			return str(e)
		if cmd is None:
			self.commandbuffer += "\n" + command
			return ''
		self.commandbuffer = ''
		oldout = sys.stdout
		class console_file(object):
			def __init__(self, copy = None):
				self.buffer = ''
				self.copy = copy
			def write(self, string):
				parts = (self.buffer + string).split("\n")
				self.buffer = parts.pop()
				for p in parts:
					game.main.fife.console.println(p)
				self.copy.write(string)
			def __del__(self):
				if len(self.buffer) > 0:
					self.write('\n')
		sys.stdout = console_file(oldout)
		try:
			exec cmd in globals()
		except BaseException, e:
			sys.stdout = oldout
			return str(e)
		sys.stdout = oldout
		return ''

	def onToolsClick(self):
		self.onConsoleCommand('import debug')
