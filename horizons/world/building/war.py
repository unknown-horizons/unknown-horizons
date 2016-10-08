# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

from horizons.constants import BUILDINGS, WEAPONS
from horizons.scheduler import Scheduler
from horizons.world.building.buildable import BuildableSingle, BuildableLine
from horizons.world.building.building import BasicBuilding
from horizons.world.units.weaponholder import StationaryWeaponHolder


class Tower(BuildableSingle, StationaryWeaponHolder, BasicBuilding):

	POSSIBLE_WEAPONS = [ WEAPONS.CANNON ]

	def __init__(self, *args, **kwargs):
		super(Tower, self).__init__(*args, **kwargs)
		# apply cannons already paid for
		for weapon_type in self.__class__.POSSIBLE_WEAPONS:
			for i in xrange(self.costs.get(weapon_type, 0)):
				self.add_weapon_to_storage(weapon_type)

	def fire_all_weapons(self, dest, rotate=True):
		super(Tower, self).fire_all_weapons(dest, rotate)

	def update_range(self, caller=None):
		self._fix_weapon_range()
		super(Tower, self).update_range(caller=caller)

	def _fix_weapon_range(self):
		"""Set all min weapon ranges to 0.
		Since the tower can't move, melee units could just approach it and
		destroy the tower"""
		for weapon in self._weapon_storage:
			weapon.weapon_range = (0, weapon.weapon_range[1])


class Barrier(BasicBuilding, BuildableLine):
	"""Buildable barriers."""

	def init(self):
		# this does not belong in __init__, it's just here that all the data should be consistent
		self.__init()

	def __init(self):
		# don't always recalculate while loading, we'd recalculate too often.
		# do it once when everything is finished.
		if not self.session.world.inited:
			Scheduler().add_new_object(self.recalculate_orientation, self, run_in=0)
		else:
			self.recalculate_surrounding_tile_orientation()
			self.recalculate_orientation()

	def remove(self):
		super(Barrier, self).remove()
		self.recalculate_surrounding_tile_orientation()

	def is_barrier(self, tile):
		# Only consider barriers that the player build
		return (tile is not None and
		        tile.object is not None and
		        tile.object.id == self.id and
		        tile.object.owner == self.owner)

	def recalculate_surrounding_tile_orientation(self):
		for tile in self.island.get_surrounding_tiles(self.position):
			if self.is_barrier(tile):
				tile.object.recalculate_orientation()

	def recalculate_orientation(self):
		"""
		ROAD ORIENTATION CHEATSHEET
		===========================
		a       b
		 \  e  /     a,b,c,d are connections to nearby roads
		  \   /
		   \ /       e,f,g,h indicate whether this area occupies more space than
		 h  X  f     a single road would (i.e. whether we should fill this three-
		   / \       cornered space with graphics that will make it look like a
		  /   \      coherent square instead of many short-circuit road circles).
		 /  g  \     Note that 'e' can only be placed if both 'a' and 'b' exist.
		d       c

		SAMPLE ROADS
		============
		\     \     \..../  \    /    \    /
		 \    .\     \../    \  /.     \  /.
		  \   ..\     \/      \/..      \/..
		  /   ../     /         ..      /\..
		 /    ./     /           .     /..\.
		/     /     /                 /....\

		ad    adh   abde   abf (im-   abcdfg
		                   possible)
		"""
		action = ''
		origin = self.position.origin

		# Order is important here.
		ordered_actions = sorted(BUILDINGS.ACTION.action_offset_dict.iteritems())
		for action_part, (xoff, yoff) in ordered_actions:
			tile = self.island.get_tile(origin.offset(xoff, yoff))
			if not self.is_barrier(tile):
				continue

			if action_part in 'abcd':
				action += action_part
			if action_part in 'efgh':
				# Now check whether we can place valid road-filled areas.
				# Only adds 'g' to action if both 'c' and 'd' are in already
				# (that's why order matters - we need to know at this point)
				# and the condition for 'g' is met: road tiles exist in that
				# direction.
				fill_left = chr(ord(action_part) - 4) in action
				# 'h' has the parents 'd' and 'a' (not 'e'), so we need a slight hack here.
				fill_right = chr(ord(action_part) - 3 - 4*(action_part=='h')) in action
				if fill_left and fill_right:
					action += action_part
		if action == '':
			# Single trail piece with no neighbor road tiles.
			action = 'single'

		location = self._instance.getLocation()
		self.act(action, location, True)
