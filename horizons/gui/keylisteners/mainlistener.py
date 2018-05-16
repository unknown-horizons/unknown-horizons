# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

import datetime
import os
import os.path
import shutil
import tempfile

from fife import fife

import horizons.globals
import horizons.main
from horizons.constants import PATHS
from horizons.util.living import LivingObject

from .keyconfig import KeyConfig


class MainListener(fife.IKeyListener, fife.ICommandListener, LivingObject):
	"""MainListener Class to process events of main window"""

	def __init__(self, gui):
		super().__init__()
		self.gui = gui
		fife.IKeyListener.__init__(self)
		horizons.globals.fife.eventmanager.addKeyListener(self)
		fife.ICommandListener.__init__(self)
		horizons.globals.fife.eventmanager.addCommandListener(self)

	def end(self):
		horizons.globals.fife.eventmanager.removeKeyListener(self)
		super().end()

	def keyPressed(self, evt):
		if evt.isConsumed():
			return

		action = KeyConfig().translate(evt)
		_Actions = KeyConfig._Actions
		keyval = evt.getKey().getValue()

		key_event_handled = True

		if action == _Actions.ESCAPE:
			self.gui.on_escape()
		elif keyval == fife.Key.ENTER:
			self.gui.on_return()
		elif action == _Actions.CONSOLE:
			self.gui.fps_display.toggle()
		elif action == _Actions.HELP:
			self.gui.on_help()
		elif action == _Actions.SCREENSHOT:
			# save the screenshot into a temporary file because fife doesn't support unicode paths
			temp_handle, temp_path = tempfile.mkstemp()
			os.close(temp_handle)
			horizons.globals.fife.engine.getRenderBackend().captureScreen(temp_path)

			# move the screenshot into the final location
			filename = datetime.datetime.now().isoformat('.').replace(":", "-") + ".png"
			final_path = os.path.join(PATHS.SCREENSHOT_DIR, filename)
			shutil.move(temp_path, final_path)

			# ingame message if there is a session and it is fully initialized:
			# pressing S on loading screen finds a session but no gui usually.
			session = horizons.main.session
			if session is not None and session.ingame_gui is not None:
				session.ingame_gui.message_widget.add('SCREENSHOT',
				                                      message_dict={'file': final_path})
		elif action == _Actions.QUICKLOAD:
			horizons.main._load_last_quicksave()
		else:
			key_event_handled = False # nope, nothing triggered

		if key_event_handled:
			evt.consume() # prevent other listeners from being called

	def keyReleased(self, evt):
		pass

	def onCommand(self, command):
		if command.getCommandType() == fife.CMD_QUIT_GAME:
			# NOTE Sometimes we get two quit events from FIFE, ignore the second
			#      if we are already shutting down the game
			if not horizons.globals.fife.quit_requested:
				horizons.main.quit()
			command.consume()
