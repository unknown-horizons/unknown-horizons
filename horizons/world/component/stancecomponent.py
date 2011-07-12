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

from horizons.world.component import Component
from horizons.util import Callback

class StanceComponent(Component):
	def __init__(self, instance):
		super(StanceComponent, self).__init__(instance)
		self.state = 'idle'
		self.action = {
			'idle' : self.act_idle,
			'user_attack' : self.act_user_attack,
			'user_move' : self.act_user_move,
			'move_back' : self.act_move_back,
			'auto_attack' : self.act_auto_attack,
			'flee' : self.act_flee,
		}
		# change state to 'user_attack' when the user issues attack via right click
		self.instance.add_user_attack_issued_listener(Callback(self.set_state, 'user_attack'))
		# change state to 'user_move' when the user issues movement via right click
		self.instance.add_user_move_issued_listener(Callback(self.set_state, 'user_move'))

	def remove(self):
		self.instance.remove_user_attack_issued_listener(Callback(self.set_state, 'user_attack'))
		self.instance.remove_user_move_issued_listener(Callback(self.set_state, 'user_move'))
		super(StanceComponent, self).remove()

	def set_state(self, state):
		self.state = state

	def get_state(self):
		return self.state

	def act(self):
		"""
		Act according to selected state
		"""
		self.action[self.state]()

	def act_idle(self):
		pass

	def act_user_attack(self):
		if not self.instance._target:
			self.state = 'idle'

	def act_user_move(self):
		if not self.instance.is_moving():
			self.state = 'idle'

	def act_move_back(self):
		self.instance.stop()
		self.state = 'idle'

	def act_auto_attack(self):
		self.instance.stop_attack()
		self.state = 'idle'

	def act_flee(self):
		self.instance.stop()
		self.state = 'idle'
