# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.

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

import logging

from horizons.component import Component
from horizons.util import Point, Circle

class CommandableComponent(Component):
	"""
	Class that handles the Commandable component of units
	"""
	log = logging.getLogger("component.commandable")

	# Store the name of this component
	NAME = 'commandable'

	def __init__(self):
		super(CommandableComponent, self).__init__()

	def go(self, x, y):
		from horizons.world.units.movingobject import MoveNotPossible
		"""Moves the unit.
		This is called when a unit is selected and the right mouse button is pressed outside the unit"""
		x = int(round(x))
		y = int(round(y))
		move_target = Point(x, y)

		try:
			self.instance.move(move_target)
		except MoveNotPossible:
			# find a near tile to move to
			surrounding = Circle(move_target, radius=1)
			move_target = None
			# try with smaller circles, increase radius if smaller circle isn't reachable
			while surrounding.radius < 5:
				try:
					self.instance.move(surrounding)
				except MoveNotPossible:
					surrounding.radius += 1
					continue
				# update actual target coord
				move_target = self.instance.get_move_target()
				break
		if self.instance.owner.is_local_player:
			self.instance.session.ingame_gui.minimap.show_unit_path(self.instance)
		if move_target is None: # can't move
			if self.instance.owner.is_local_player:
				if self.session.world.get_tile(Point(x, y)) is None: # not even in world
					self.session.ingame_gui.message_widget.add(point=Point(x, y), string_id="MOVE_OUTSIDE_OF_WORLD")
				else: # in world, but still unreachable
					self.session.ingame_gui.message_widget.add(point=Point(x, y), string_id="MOVE_INVALID_LOCATION")
			return None
