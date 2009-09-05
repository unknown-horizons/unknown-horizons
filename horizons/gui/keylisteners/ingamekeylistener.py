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
import horizons.main

from horizons.util.living import LivingObject
from horizons.gui.mousetools import BuildingTool

class IngameKeyListener(fife.IKeyListener, LivingObject):
	"""KeyListener Class to process key presses ingame"""

	def __init__(self):
		super(IngameKeyListener, self).__init__()
		horizons.main.fife.eventmanager.addKeyListener(self)
		self.keysPressed = []

	def end(self):
		horizons.main.fife.eventmanager.removeKeyListener(self)
		super(IngameKeyListener, self).end()

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		keystr = evt.getKey().getAsString().lower()

		was = keyval in self.keysPressed
		if not was:
			self.keysPressed.append(keyval)
		if keyval == fife.Key.LEFT:
			if not was: horizons.main.session.view.autoscroll(-25, 0)
		elif keyval == fife.Key.RIGHT:
			if not was: horizons.main.session.view.autoscroll(25, 0)
		elif keyval == fife.Key.UP:
			if not was: horizons.main.session.view.autoscroll(0, -25)
		elif keyval == fife.Key.DOWN:
			if not was: horizons.main.session.view.autoscroll(0, 25)
		elif keystr == 'g':
			horizons.main.session.view.renderer['GridRenderer'].setEnabled(not horizons.main.session.view.renderer['GridRenderer'].isEnabled())
		elif keystr == 'x':
			horizons.main.session.destroy_tool()
		elif keystr == '+':
			horizons.main.session.speed_up()
		elif keystr == '-':
			horizons.main.session.speed_down()
		elif keystr == 'p':
			horizons.main.gui.toggle_ingame_pause()
		elif keystr == 'd':
			import pdb; pdb.set_trace()
		elif keystr == 'b':
			horizons.main.session.ingame_gui.show_build_menu()
		elif keystr == '.':
			if isinstance(horizons.main.session.cursor, BuildingTool):
				horizons.main.session.cursor.rotate_right()
		elif keystr == ',':
			if isinstance(horizons.main.session.cursor, BuildingTool):
				horizons.main.session.cursor.rotate_left()
		elif keyval in (fife.Key.NUM_0, fife.Key.NUM_1, fife.Key.NUM_2, fife.Key.NUM_3, fife.Key.NUM_4, fife.Key.NUM_5, fife.Key.NUM_6, fife.Key.NUM_7, fife.Key.NUM_8, fife.Key.NUM_9):
			num = int(keyval - fife.Key.NUM_0)
			if evt.isControlPressed():
				horizons.main.session.selection_groups[num] = horizons.main.session.selected_instances.copy()
				for group in horizons.main.session.selection_groups:
					if group is not horizons.main.session.selection_groups[num]:
						group -= horizons.main.session.selection_groups[num]
			else:
				for instance in horizons.main.session.selected_instances - horizons.main.session.selection_groups[num]:
					instance.deselect()
				for instance in horizons.main.session.selection_groups[num] - horizons.main.session.selected_instances:
					instance.select()
				horizons.main.session.selected_instances = horizons.main.session.selection_groups[num]
		elif keyval == fife.Key.F5:
			horizons.main.session.quicksave()
		elif keyval == fife.Key.F9:
			horizons.main.session.quickload()
		else:
			return
		evt.consume()

	def keyReleased(self, evt):
		keyval = evt.getKey().getValue()
		try:
			self.keysPressed.remove(keyval)
		except:
			return
		if keyval == fife.Key.LEFT:
			horizons.main.session.view.autoscroll(25, 0)
		elif keyval == fife.Key.RIGHT:
			horizons.main.session.view.autoscroll(-25, 0)
		elif keyval == fife.Key.UP:
			horizons.main.session.view.autoscroll(0, 25)
		elif keyval == fife.Key.DOWN:
			horizons.main.session.view.autoscroll(0, -25)
