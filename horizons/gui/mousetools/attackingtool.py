# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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
from horizons.command.unit import Act
from horizons.util import WorldObject
from selectiontool import SelectionTool
from horizons.constants import LAYERS

class AttackingTool(SelectionTool):
	#NOTE bug with selecting other units (tab not shown)
	#also keylisteners don't work
	"""
		This will be used when attacking units are selected
		it will have to respond on right click and change cursor image when hovering enemy units
	"""
	def __init__(self, session):
		super(AttackingTool, self).__init__(session)
		print 'attacking tool selected'

	def mousePressed(self, evt):
		#NOTE for testing, catches only one right click event, then reverts to selection tool
		if (evt.getButton() == fife.MouseEvent.RIGHT):
			target_mapcoord = self.session.view.cam.toMapCoordinates(\
				fife.ScreenPoint(evt.getX(), evt.getY()), False)

			target = self._get_attackable_instance(evt)

			if target:
				for i in self.session.selected_instances:
					#TODO attack command
					#dummy attack if possible
					if hasattr(i, 'attack'):
						i.attack(target)
			else:
				for i in self.session.selected_instances:
					if i.movable:
						Act(i, target_mapcoord.x, target_mapcoord.y).execute(self.session)
			evt.consume()
		else:
			super(AttackingTool, self).mousePressed(evt)

	def mouseMoved(self, evt):
		super(AttackingTool, self).mouseMoved(evt)
		target = self._get_attackable_instance(evt)
		if target:
			horizons.main.fife.cursor.set(fife.CURSOR_IMAGE, horizons.main.fife.attacking_cursor_image)
		else:
			horizons.main.fife.cursor.set(fife.CURSOR_IMAGE, horizons.main.fife.default_cursor_image)

	def _get_attackable_instance(self, evt):
		"""
		Returns target instance if mouse is over an attackable instance
		Returns None if mouse is not over an attackable instance
		"""
		instances = self.session.view.cam.getMatchingInstances(\
			fife.ScreenPoint(evt.getX(), evt.getY()), self.session.view.layers[LAYERS.OBJECTS])

		target = None
		attackable = False
		for i in instances:
			id = i.getId()
			if id == '':
				continue
			instance = WorldObject.get_object_by_id(int(id))
			local_player = self.session.world.player
			if not instance.owner:
				continue
			#check diplomacy state between local player and instance owner
			if not self.session.world.diplomacy.are_enemies(local_player, instance.owner):
				continue
			#NOTE attacks only buildings or ships
			try:
				if instance.is_building or instance.is_ship:
					attackable = True
					target = instance
			except AttributeError:
				pass
		return target

