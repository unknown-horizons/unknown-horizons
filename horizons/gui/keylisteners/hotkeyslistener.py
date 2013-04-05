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

from fife import fife
import horizons.globals
from horizons.gui.keylisteners import KeyConfig
from horizons.util.living import LivingObject
from horizons.constants import PATHS

class HotkeysListener(fife.IKeyListener, fife.ICommandListener, LivingObject):
	"""HotkeysListener Class to process events of hotkeys binding interface"""

	def __init__(self):
		super(HotkeysListener, self).__init__()
		fife.IKeyListener.__init__(self)
		horizons.globals.fife.eventmanager.addKeyListenerFront(self)
		fife.ICommandListener.__init__(self)
		horizons.globals.fife.eventmanager.addCommandListener(self)

	def end(self):
		horizons.globals.fife.eventmanager.removeKeyListener(self)
		super(HotkeysListener, self).end()

	def keyPressed(self, evt):
		print 'hotkey_listener detected keypress'
		evt.consume()

	def keyReleased(self, evt):
		pass

	def onCommand(self, command):
		if command.getCommandType() == fife.CMD_QUIT_GAME:
			horizons.main.quit()
			command.consume()
