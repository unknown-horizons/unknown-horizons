# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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
from typing import ClassVar

from horizons.component import Component
from horizons.util.shapes import Circle, Point
from horizons.world.units.unitexeptions import MoveNotPossible

MAX_FALLBACK_RADIUS: int = 4


class CommandableComponent(Component):
	"""
	Class that handles the Commandable component of units
	"""
	log = logging.getLogger("component.commandable")

	# Store the name of this component
	NAME: ClassVar[str] = "commandable"

	def __init__(self) -> None:
		super().__init__()

	def go(self, x: float, y: float) -> None:
		"""Move the unit toward the given coordinates, trying nearby positions if needed."""
		x = int(round(x))
		y = int(round(y))
		move_target = Point(x, y)

		try:
			self.instance.move(move_target)
		except MoveNotPossible:
			# Try nearby circles with increasing radii.
			for radius in range(1, MAX_FALLBACK_RADIUS + 1):
				try:
					self.instance.move(Circle(move_target, radius=radius))
				except MoveNotPossible:
					continue

				# A fallback move succeeded.
				move_target = self.instance.get_move_target()
				break
			else:
				# No fallback move succeeded.
				move_target = None

		if self.instance.owner.is_local_player:
			self.instance.session.ingame_gui.minimap.show_unit_path(self.instance)

		if move_target is None:
			if not self.instance.owner.is_local_player:
				return

			if self.session.world.get_tile(Point(x, y)) is None: # Not even in world
				string_id = "MOVE_OUTSIDE_OF_WORLD"
			else: # In world, but still unreachable
				string_id = "MOVE_INVALID_LOCATION"

			self.session.ingame_gui.message_widget.add(
				point=Point(x, y),
				string_id=string_id,
			)
