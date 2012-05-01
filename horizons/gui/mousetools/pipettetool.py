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

import horizons.main

from horizons.entities import Entities
from horizons.constants import LAYERS, BUILDINGS
from horizons.gui.mousetools import  NavigationTool
from horizons.gui.tabs.buildtabs import BuildTab
from horizons.component.ambientsoundcomponent import AmbientSoundComponent


class PipetteTool(NavigationTool):
	"""Tool to select buildings in order to build another building of
	the type of the selected building"""
	HIGHLIGHT_COLOR = (0, 200, 90)
	HIGHLIGHT_NOT_POSSIBLE_COLOR = (200, 90, 90)

	def __init__(self, session):
		super(PipetteTool, self).__init__(session)
		self.session.gui.on_escape = self.on_escape
		self.renderer = session.view.renderer['InstanceRenderer']
		horizons.main.fife.set_cursor_image('pipette')

	def remove(self):
		self._remove_coloring()
		horizons.main.fife.set_cursor_image('default')
		super(PipetteTool, self).remove()

	def on_escape(self):
		self.session.set_cursor()

	def mouseMoved(self,  evt):
		self.update_coloring(evt)

	def mousePressed(self,  evt):
		if evt.getButton() == fife.MouseEvent.LEFT:
			obj = self._get_object(evt)
			if obj and self._is_buildable(obj.id):
				self.session.set_cursor('building', Entities.buildings[obj.id])
			elif obj: # object that is not buildable
				AmbientSoundComponent.play_special('error')
				self.on_escape()
			else:
				self.on_escape()
			evt.consume()
		elif evt.getButton() == fife.MouseEvent.RIGHT:
			self.on_escape()
			evt.consume()
		else:
			super(PipetteTool,  self).mouseClicked(evt)

	def _get_object(self, evt):
		for obj in self.get_hover_instances(evt, layers=[LAYERS.FIELDS, LAYERS.OBJECTS]):
			if obj.id in Entities.buildings:
				return obj
		return None

	def update_coloring(self, evt):
		obj = self._get_object(evt)
		self._remove_coloring()
		if obj:
			self._add_coloring(obj)

	def _is_buildable(self, building_id):
		building_increments = BuildTab.get_building_increments()
		return building_id in building_increments and \
					 building_increments[ building_id ] <= self.session.world.player.settler_level

	def _add_coloring(self,  obj):
		if self._is_buildable(obj.id):
			self.renderer.addColored(obj.fife_instance,
			                         *self.__class__.HIGHLIGHT_COLOR)
		else:
			self.renderer.addColored(obj.fife_instance,
			                         *self.__class__.HIGHLIGHT_NOT_POSSIBLE_COLOR)

	def _remove_coloring(self):
		self.renderer.removeAllColored()
