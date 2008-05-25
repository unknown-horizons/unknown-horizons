# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

class MainListener(fife.IKeyListener, fife.ConsoleExecuter):
	"""MainListener Class to process events of main window"""

	def __init__(self):
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

	def __del__(self):
		game.main.fife.eventmanager.removeKeyListener(self)

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		if keyval == fife.Key.ESCAPE:
			if game.main.gui.isVisible() and game.main.game is not None:
				game.main.gui.hide()
			elif game.main.gui.isVisible():
				game.main.showQuit()
			elif not game.main.gui.isVisible():
				game.main.gui.show()
			evt.consume()
		elif keyval == fife.Key.F10:
			game.main.fife.console.toggleShowHide()
			evt.consume()

	def keyReleased(self, evt):
		pass

	def onCommand(self, command):
		if command.getCommandType() == fife.CMD_QUIT_GAME:
			game.main.fife.quit()
			command.consume()

	def onConsoleCommand(self, command):
		try:
			cmd = code.compile_command(self.commandbuffer + command)
			if cmd == None:
				self.commandbuffer += command
			else:
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
				exec cmd in globals()
				sys.stdout = oldout
		except Exception, e:
			return str(e)
		return ''

	def onToolsClick(self):
		pass
