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


from horizons.world.component import Component
from horizons.util import Point
from horizons.world.units.movingobject import MoveNotPossible


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
		"""Moves the unit.
		This is called when a unit is selected and the right mouse button is pressed outside the unit"""
		move_target = Point(int(round(x)), int(round(y)))
		try:
			self.move(move_target)
		except MoveNotPossible:
			# find a near tile to move to
			surrounding = Circle(move_target, radius=1)
			move_target = None
			# try with smaller circles, increase radius if smaller circle isn't reachable
			while surrounding.radius < 5:
				try:
					self.move(surrounding)
				except MoveNotPossible:
					surrounding.radius += 1
					continue
				# update actual target coord
				move_target = self.get_move_target()
				break

		if move_target is None: # can't move
			# TODO: give player some kind of feedback
			return
