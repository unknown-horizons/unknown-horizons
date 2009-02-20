# ###################################################
# Copyright (C) 2008 The Unknown Horizons Team
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

import math
import weakref
from game.util import WeakMethod

import game.main

class Growable(object):
	""" Base class for everything that grows
	Growing means, that the object changes it's apperance
	after a certain amount of time

	Subclasses have to provide self.db_actions

	IDEA: maybe store reference to production building,
	      if such exists, here
	"""
	def __init__(self, producer, **kwargs):
		"""
		@param producer: producer that determines animation change intervals and such
		"""
		super(Growable, self).__init__(producer=producer, **kwargs)
		self.growing_producer = weakref.ref(producer)
		self.growing_producer().restart_animation = WeakMethod(self.restart_animation)
		self.actions = []
		self.db_actions = game.main.db("SELECT action FROM data.action WHERE action_set_id = ? AND action != 'default'", self._action_set_id)
		for (a,) in self.db_actions:
			self.actions.append(a)
		self.actions.sort()
		self.restart_animation()

	# FIXME: This ugly hack removes the cyclic reference of most Growables
	# FIXME: Please fix this fucked up class in the first place
	def remove(self):
		del self.growing_producer().restart_animation
		del self.growing_producer
		super(Growable, self).remove()

	# parts of the following code is to difficult to comment
	# but it works, trust me ;-)
	def next_animation(self):
		return
		""" Executes next action """
		import time
		#print 'CALLED NEXT_ANI, id',self.id,self, "AT", time.time()
		try:
			self.action = self.action_iter.next()
		except StopIteration:
			return

		self._instance.act(self.action, self._instance.getLocation(), True)

		iter_pos = len(self.actions) - self.action_iter.__length_hint__()
		#if self.loop_until < (len(self.actions) - self.action_iter.__length_hint__()):
		if self.loop_until < iter_pos:
			# producer called next_animation because new item was produced
			if self.action_iter.__length_hint__() == 0:
				# reached last animation, don't schedule another call to this fun
				return
			self.growing_info = self.growing_producer.get_growing_info()
			#interval = self.growing_info[3]/(len(self.actions)-1)
			interval = self.growing_info[3]/(len(self.actions)-1)
			#print 'INTER', interval
			# loop_until = floor ( num_actions-1 / production_storage_size ) * max(1, cur_production_amount)
			# -1 because the fun already did the work in the head of this fun

			self.loop_until = int(math.floor(((len(self.actions)-1) / self.growing_info[2]) * max(1, self.growing_info[1])))
			loops = self.loop_until - iter_pos
			#print 'UNTIL', self.loop_until
			#print 'ITER ', iter_pos
			#print 'LOOPS', loops
			if loops > 0:
				game.main.session.scheduler.add_new_object(self.next_animation, self, interval, loops)

	def restart_animation(self):
		""" Starts animation from the beginning

		Useful if e.g. a tree is cut down
		"""
		#print 'RESTARTING ANI, id',self.id,self
		self.action_iter = iter(self.actions)
		self.loop_until = -1 # force recalculation
		self.next_animation()
