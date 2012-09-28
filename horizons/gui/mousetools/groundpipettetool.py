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

import horizons.globals

from horizons.constants import GROUND
from horizons.gui.mousetools import NavigationTool

class GroundPipetteTool(NavigationTool):
	"""Tool that copies ground tiles."""
	HIGHLIGHT_COLOR = (0, 200, 90)

	def __init__(self, session):
		super(GroundPipetteTool, self).__init__(session)
		self.session.gui.on_escape = self.on_escape
		self.renderer = session.view.renderer['InstanceRenderer']
		horizons.globals.fife.set_cursor_image('pipette')

	def remove(self):
		self._remove_coloring()
		horizons.globals.fife.set_cursor_image('default')
		super(GroundPipetteTool, self).remove()

	def on_escape(self):
		self.session.set_cursor()

	def mouseMoved(self, evt):
		self.update_coloring(evt)

	def _get_tile_details(self, coords):
		if coords in self.session.world.full_map:
			tile = self.session.world.full_map[coords]
			if tile.id == -1:
				return GROUND.WATER
			else:
				return (tile.id, tile._action, tile._instance.getRotation() + 45)
		else:
			return GROUND.WATER

	def mousePressed(self, evt):
		if evt.getButton() == fife.MouseEvent.LEFT:
			tile_details = self._get_tile_details(self.get_world_location(evt).to_tuple())
			self.session.set_cursor('tile_layer', tile_details)
			evt.consume()
		elif evt.getButton() == fife.MouseEvent.RIGHT:
			self.on_escape()
			evt.consume()
		else:
			super(GroundPipetteTool, self).mouseClicked(evt)

	def update_coloring(self, evt):
		self._remove_coloring()
		self._add_coloring(self.get_world_location(evt).to_tuple())

	def _add_coloring(self, coords):
		if coords in self.session.world.full_map:
			tile = self.session.world.full_map[coords]
			if hasattr(tile, '_instance'):
				self.renderer.addColored(tile._instance, *self.HIGHLIGHT_COLOR)

	def _remove_coloring(self):
		self.renderer.removeAllColored()
