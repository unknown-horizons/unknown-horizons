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

from horizons.entities import Entities
from horizons.constants import LAYERS
from horizons.gui.mousetools import NavigationTool
from horizons.gui.tabs.buildtabs import BuildTab

class TileLayingTool(NavigationTool):
	"""Tool to lay ground tiles."""

	def __init__(self, session, tile_details):
		super(TileLayingTool, self).__init__(session)
		self.session.gui.on_escape = self.on_escape
		self.renderer = session.view.renderer['InstanceRenderer']
		self._tile_details = tile_details
		# TODO: use the right tile's image
		horizons.globals.fife.set_cursor_image('default')

	def remove(self):
		self._remove_coloring()
		horizons.globals.fife.set_cursor_image('default')
		super(TileLayingTool, self).remove()

	def on_escape(self):
		self.session.set_cursor()

	def mouseMoved(self, evt):
		self.update_coloring(evt)

	def mousePressed(self, evt):
		if evt.getButton() == fife.MouseEvent.LEFT:
			coords = self.get_world_location(evt).to_tuple()
			self.session.world_editor.set_tile(coords, self._tile_details)
			evt.consume()
		elif evt.getButton() == fife.MouseEvent.RIGHT:
			self.on_escape()
			evt.consume()
		else:
			super(PipetteTool, self).mouseClicked(evt)

	def update_coloring(self, evt):
		self._remove_coloring()
		self._add_coloring(self.get_world_location(evt).to_tuple())

	def _add_coloring(self, pos):
		pass

	def _remove_coloring(self):
		self.renderer.removeAllColored()
