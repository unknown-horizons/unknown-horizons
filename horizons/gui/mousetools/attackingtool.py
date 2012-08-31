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
from horizons.command.unit import Act, Attack
from horizons.command.diplomacy import AddEnemyPair
from horizons.component.healthcomponent import HealthComponent
from horizons.gui.mousetools.selectiontool import SelectionTool

class AttackingTool(SelectionTool):
	"""
		This will be used when attacking units are selected
		it will have to respond on right click and change cursor image when hovering enemy units
	"""

	send_hover_instances_update = False

	def __init__(self, session):
		super(AttackingTool, self).__init__(session)

	def mousePressed(self, evt):
		if evt.getButton() == fife.MouseEvent.RIGHT:
			target_mapcoord = self.session.view.cam.toMapCoordinates(
				fife.ScreenPoint(evt.getX(), evt.getY()), False)

			target = self._get_attackable_instance(evt)

			if target:
				if not self.session.world.diplomacy.are_enemies(self.session.world.player, target.owner):
					AddEnemyPair(self.session.world.player, target.owner).execute(self.session)
				for i in self.session.selected_instances:
					if hasattr(i, 'attack'):
						Attack(i, target).execute(self.session)
			else:
				for i in self.session.selected_instances:
					if i.movable:
						Act(i, target_mapcoord.x, target_mapcoord.y).execute(self.session)
			evt.consume()
		else:
			self.deselect_at_end = False
			super(AttackingTool, self).mousePressed(evt)

	def mouseMoved(self, evt):
		super(AttackingTool, self).mouseMoved(evt)
		target = self._get_attackable_instance(evt)
		if target:
			horizons.main.fife.set_cursor_image("attacking")
		else:
			horizons.main.fife.set_cursor_image("default")

	def _get_attackable_instance(self, evt):
		"""
		Returns target instance if mouse is over an attackable instance
		Returns None if mouse is not over an attackable instance
		"""
		instances = self.get_hover_instances(evt)

		target = None
		local_player = self.session.world.player
		for instance in instances:
			if not instance.owner:
				continue

			if instance.owner is local_player:
				continue

			#check diplomacy state between local player and instance owner
			if not self.session.world.diplomacy.are_enemies(local_player, instance.owner) \
				and not evt.isShiftPressed():
				continue
			if instance.has_component(HealthComponent):
				target = instance
		return target

