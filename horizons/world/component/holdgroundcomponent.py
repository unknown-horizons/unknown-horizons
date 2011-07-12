# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from horizons.world.component.stancecomponent import StanceComponent
from horizons.util import Circle
from horizons.world.units.movingobject import MoveNotPossible

class HoldGroundComponent(StanceComponent):
	"""
	Stance that makes the unit defend with a limited area of action
	"""
	def __init__(self, instance):
		super(HoldGroundComponent, self).__init__(instance)
		#TODO get range from db
		self.stance_range = 5
		# get a copy of the center Point object
		self.return_position = self.instance.position.center().copy()

	def act_idle(self):
		"""
		Find target in range then attack it
		"""
		target = self.get_target()
		if target:
			self.instance.attack(target)
			self.state = 'auto_attack'

	def act_user_move(self):
		"""
		At the end of user move change the returning position for which to hold ground
		"""
		if not self.instance.is_moving():
			self.state = 'idle'
			self.return_position = self.instance.position.center().copy()

	def act_user_attack(self):
		"""
		If attack ends, move update the returning position to current position and continue stance
		"""
		if not self.instance.is_attacking():
			self.state = 'idle'
			self.return_position = self.instance.position.center().copy()

	def act_move_back(self):
		"""
		When moving back try to find target. If found, attack it and drop movement
		"""
		target = self.get_target()
		if target:
			self.instance.attack(target)
			self.state = 'auto_attack'
		elif self.instance.position.center() == self.return_position:
			self.state = 'idle'

	def act_auto_attack(self):
		"""
		Check if target still exists or if unit exited the hold ground area
		"""
		if not Circle(self.return_position, self.stance_range).contains(self.instance.position.center()) or \
			not self.instance.is_attacking():
				try:
					self.instance.move(self.return_position)
					self.state = 'move_back'
				except MoveNotPossible:
					pass

	def get_target(self):
		"""
		Gets the closest enemy in unit's max range added to stances range
		"""
		enemies = [u for u in self.instance.session.world.get_ships(self.instance.position.center(), self.instance._max_range + self.stance_range) \
			if self.instance.session.world.diplomacy.are_enemies(u.owner, self.instance.owner)]

		if not enemies:
			return None

		return sorted(enemies, key = lambda e: self.instance.position.distance(e.position))[0]

