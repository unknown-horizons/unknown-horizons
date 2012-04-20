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

from horizons.component import Component
from horizons.util import Callback, Circle, Annulus
from horizons.scheduler import Scheduler

class StanceComponent(Component):
	"""
	Class to be inherited for all unit stances
	It has methods defined for specific instance states
	The default methods are defined that the instance only listens to user commands
	If a state different from user_attack or user_move is passed, it stops any action
	and switches to idle.

	NOTE:
	This does not use stance inheritance as intended, but multiple stance
	components are present at the same time, while only one is used at a time.
	"""

	# Store the name of this component
	NAME = 'stance'

	def __init__(self):
		super(StanceComponent, self).__init__()
		self.state = 'idle'
		self.action = {
		    'idle' : self.act_idle,
		    'user_attack' : self.act_user_attack,
		    'user_move' : self.act_user_move,
		    'move_back' : self.act_move_back,
		    'auto_attack' : self.act_auto_attack,
		    'flee' : self.act_flee,
		}

	def initialize(self):
		# change state to 'user_attack' when the user issues attack via right click
		self.instance.add_user_attack_issued_listener(Callback(self.set_state, 'user_attack'))
		# change state to 'user_move' when the user issues movement via right click
		try:
			self.instance.add_user_move_issued_listener(Callback(self.set_state, 'user_move'))
		except AttributeError:
			pass # temporary workaround to make it work for towers

	def remove(self):
		self.instance.remove_user_attack_issued_listener(Callback(self.set_state, 'user_attack'))
		try:
			self.instance.remove_user_move_issued_listener(Callback(self.set_state, 'user_move'))
		except AttributeError:
			pass # temporary workaround to make it work for towers
		super(StanceComponent, self).remove()

	def set_state(self, state):
		self.state = state

	def get_state(self):
		return self.state

	def act(self):
		"""
		Act according to current state
		This is called every few second in the instance code
		"""
		self.action[self.state]()

	def act_idle(self):
		"""
		Method executed when the instance is idle
		"""
		pass

	def act_user_attack(self):
		"""
		Method executed when the instance is trying to attack a target selected by the user
		"""
		if not self.instance.is_attacking():
			self.state = 'idle'

	def act_user_move(self):
		"""
		Method executed when the instance is moving to a location selected by the user
		"""
		if not self.instance.is_moving():
			self.state = 'idle'

	def act_move_back(self):
		"""
		Method executed when the instance is moving back to it's default location
		"""
		self.instance.stop()
		self.state = 'idle'

	def act_auto_attack(self):
		"""
		Method executed when the instance has auto acquired target
		"""
		self.instance.stop_attack()
		self.state = 'idle'

	def act_flee(self):
		"""
		Method executed when the instance is trying to evade an attack
		"""
		self.instance.stop()
		self.state = 'idle'


class LimitedMoveStance(StanceComponent):
	"""
	Stance that attacks any unit in stance range and follows it with limited move space
	This is inherited by Aggressive and Hold Ground stances
	In adition to StanceComponent it has the following attributes:
		stance_radius - int with the radius in which instance shold look for target
		move_range - int with the radius in which instance shold move when attacking it
	It also keeps track of the return position in which the unit should return when stopped attacking
	"""

	def __init__(self):
		super(LimitedMoveStance, self).__init__()
		#TODO get range from db
		self.stance_radius = 0
		self.move_range = 0
		# get instance data after it was inited
		Scheduler().add_new_object(self.get_instance_data, self, run_in = 0)

	def get_instance_data(self):
		# get a copy of the center Point object
		self.return_position = self.instance.position.center().copy()

	def act_idle(self):
		"""
		Find target in range then attack it
		"""
		target = self.get_target(self.stance_radius + self.instance._max_range)
		if target:
			self.instance.attack(target)
			self.state = 'auto_attack'

	def act_user_move(self):
		"""
		At the end of user move change the returning position
		"""
		if not self.instance.is_moving():
			self.state = 'idle'
			self.return_position = self.instance.position.center().copy()

	def act_user_attack(self):
		"""
		If attack ends, update the returning position
		"""
		if not self.instance.is_attacking():
			self.state = 'idle'
			self.return_position = self.instance.position.center().copy()

	def act_move_back(self):
		"""
		When moving back try to find target. If found, attack it and drop movement
		"""
		target = self.get_target(self.stance_radius + self.instance._max_range)
		if target:
			self.instance.attack(target)
			self.state = 'auto_attack'
		elif self.instance.position.center() == self.return_position:
			self.state = 'idle'

	def act_auto_attack(self):
		"""
		Check if target still exists or if unit exited the hold ground area
		"""
		if not Circle(self.return_position, self.move_range).contains(self.instance.position.center()) or \
			not self.instance.is_attacking():
			from horizons.world.units.movingobject import MoveNotPossible
			try:
				self.instance.move(self.return_position)
			except MoveNotPossible:
				self.instance.move(Circle(self.return_position, self.stance_radius))
			self.state = 'move_back'

	def get_target(self, radius):
		"""
		Returns closest attackable unit in radius
		"""
		enemies = [u for u in self.session.world.get_health_instances(self.instance.position.center(), radius) \
		           if self.session.world.diplomacy.are_enemies(u.owner, self.instance.owner)]

		if not enemies:
			return None

		return min(enemies, key = lambda e: self.instance.position.distance(e.position))

class AggressiveStance(LimitedMoveStance):
	"""
	Stance that attacks units in close range when doing movement
	"""

	NAME = 'aggressive_stance'

	def __init__(self):
		super(AggressiveStance, self).__init__()
		#TODO get range from db
		self.stance_radius = 15
		self.move_range = 25

	def act_user_move(self):
		"""
		Check if it can attack while moving
		"""
		super(AggressiveStance, self).act_user_move()
		target = self.get_target(self.instance._max_range)
		if target:
			self.instance.fire_all_weapons(target.position.center())

	def act_user_attack(self):
		"""
		Check if can attack while moving to another attack
		"""
		super(AggressiveStance, self).act_user_attack()
		target = self.get_target(self.instance._max_range)
		if target:
			self.instance.fire_all_weapons(target.position.center())

class HoldGroundStance(LimitedMoveStance):

	NAME = 'hold_ground_stance'

	def __init__(self):
		super(HoldGroundStance, self).__init__()
		self.stance_radius = 5
		self.move_range = 15

class NoneStance(StanceComponent):

	NAME = 'none_stance'

	pass

class FleeStance(StanceComponent):
	"""
	Move away from any approaching units
	"""

	NAME = 'flee_stance'

	def __init__(self):
		super(FleeStance, self).__init__()
		self.lookout_distance = 20

	def act_idle(self):
		"""
		If an enemy unit approaches move away from it
		"""
		unit = self.get_approaching_unit()
		if unit:
			from horizons.world.units.movingobject import MoveNotPossible
			try:
				distance = unit._max_range + self.lookout_distance
				self.instance.move(Annulus(unit.position.center(), distance, distance + 2))
				self.state = 'flee'
			except MoveNotPossible:
				pass

	def act_flee(self):
		"""
		If movemen stops, switch to idle
		"""
		if not self.instance.is_moving():
			self.state = 'idle'
			# check again for target and move
			self.act_idle()

	def get_approaching_unit(self):
		"""
		Gets the closest unit that can fire to instance
		"""
		enemies = [u for u in self.session.world.get_health_instances(self.instance.position.center(), self.lookout_distance) \
		           if self.session.world.diplomacy.are_enemies(u.owner, self.instance.owner) and hasattr(u, '_max_range')]

		if not enemies:
			return None

		return min(enemies, key = lambda e: self.instance.position.distance(e.position) + e._max_range)


DEFAULT_STANCES = [ HoldGroundStance, AggressiveStance, NoneStance, FleeStance ]