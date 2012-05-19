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

import time
import horizons.main

from horizons.util.living import LivingObject
from horizons.constants import GAME_SPEED
from horizons.scheduler import Scheduler
from horizons.messaging import GameSpeedChanged
from horizons.extscheduler import ExtScheduler

class Timer(LivingObject):
	"""
	The Timer class manages game-ticks, every tick executes a set of functions in its call lists,
	this is especially important for multiplayer, to allow synchronous play.
	"""
	TEST_PASS, TEST_SKIP = xrange(0, 2)

	ACCEPTABLE_TICK_DELAY = 0.2 # sec
	DEFER_TICK_ON_DELAY_BY = 0.4 # sec


	def __init__(self, tick_next_id = Scheduler.FIRST_TICK_ID, freeze_protection=False):
		"""
		NOTE: timer will not start until activate() is called
		@param tick_next_id: int next tick id
		@param freeze_protection: whether to check for tick delay and strech time in case (breaks mp)
		"""
		super(Timer, self).__init__()
		self._freeze_protection = freeze_protection
		self.__ticks_per_second = GAME_SPEED.TICKS_PER_SECOND
		self.tick_next_id = tick_next_id
		self.tick_next_time = None
		self.tick_func_test = []
		self.tick_func_call = []
		self.gamespeedmanager = GameSpeedManager(self)

	def activate(self):
		"""Actually starts the timer"""
		horizons.main.fife.pump.append(self.check_tick)

	def end(self):
		if self.check_tick in horizons.main.fife.pump:
			horizons.main.fife.pump.remove(self.check_tick)
		self.gamespeedmanager.end()
		super(Timer, self).end()

	@property
	def ticks_per_second(self):
		return self.__ticks_per_second

	@ticks_per_second.setter
	def ticks_per_second(self, ticks):
		old = self.__ticks_per_second
		self.__ticks_per_second = ticks
		if old == 0 and self.tick_next_time is None: #back from paused state
			if self.paused_time_missing is None:
				# happens if e.g. a dialog pauses the game during startup on hotkeypress
				self.tick_next_time = time.time()
			else:
				self.tick_next_time = time.time() + (self.paused_time_missing / ticks)
		elif ticks == 0 or self.tick_next_time is None:
			# go into paused state or very early speed change (before any tick)
			if self.tick_next_time is not None:
				self.paused_time_missing = (self.tick_next_time - time.time()) * old
			else:
				self.paused_time_missing =  None
			self.tick_next_time = None
		else:
			"""
			Under odd circumstances (anti-freeze protection just activated, game speed
			decremented multiple times within this frame) this can delay the next tick
			by minutes. Since the positive effects of the code aren't really observeable,
			this code is commented out and possibly will be removed.

			# correct the time until the next tick starts
			time_to_next_tick = self.tick_next_time - time.time()
			if time_to_next_tick > 0: # only do this if we aren't late
				self.tick_next_time += (time_to_next_tick * old / ticks)
			"""

		GameSpeedChanged.broadcast(self, self.gamespeedmanager.get_actual_ticks_per_second())


	def add_test(self, call):
		"""Adds a call to the test list
		@param call: function function which should be added
		"""
		self.tick_func_test.append(call)

	def add_call(self, call):
		"""Adds a call to the call list
		@param call: function function which should be added
		"""
		self.tick_func_call.append(call)

	def remove_test(self, call):
		"""Removes a call from the test list
		@param call: function function which were added before
		"""
		self.tick_func_test.remove(call)

	def remove_call(self, call):
		"""Removes a call from the call list
		@param call: function function which were added before
		"""
		self.tick_func_call.remove(call)

	def get_ticks(self, seconds):
		"""Returns the number of ticks for the specified number of seconds.
		@param seconds: number of seconds that are to be converted into ticks
		@return: int
		"""
		return int(round( seconds*GAME_SPEED.TICKS_PER_SECOND))

	def _get_next_tick_time(self):
		ticks_per_second = self.gamespeedmanager.get_actual_ticks_per_second() if self._freeze_protection else self.ticks_per_second
		return (self.tick_next_time or time.time()) + \
		       ( 1.0 / self.gamespeedmanager.get_actual_ticks_per_second() )

	def check_tick(self):
		"""check_tick is called by the engines _pump function to signal a frame idle."""
		if self.ticks_per_second == 0:
			return
		while time.time() >= self.tick_next_time:
			for f in self.tick_func_test:
				r = f(self.tick_next_id)
				if r == self.TEST_SKIP:
					# If a callback changed the speed to zero, we have to exit
					if self.ticks_per_second != 0:
						self.tick_next_time = self._get_next_tick_time()
					return
			if self._freeze_protection and self.tick_next_time: # check if it's not the first run
				# stretch time if we're too slow
				diff = time.time() - self.tick_next_time
				self.gamespeedmanager.delays.append(diff)
				if diff > self.ACCEPTABLE_TICK_DELAY:
					print 'major delay, freeze protection kicking in ', diff, time.time()
					self.tick_next_time += self.DEFER_TICK_ON_DELAY_BY
			for f in self.tick_func_call:
				f(self.tick_next_id)
			self.tick_next_id += 1


			if self.ticks_per_second == 0:
				# If a callback changed the speed to zero, we have to exit
				return
			self.tick_next_time = self._get_next_tick_time()


class GameSpeedManager(object):
	"""Keeps track of the performance of the machine and suggests slighlty changed game speeds
	such that the game runs smoothly

	http://wiki.unknown-horizons.org/w/Dynamic_game_speed
	"""

	# if the ticks delay is nearly as big as the time it takes to calculate,
	# we're close to overlaps
	AVG_DELAY_THRESHOLD = (1.0 / GAME_SPEED.TICKS_PER_SECOND) * 0.65 # ~= 0.04

	STEPS = 4

	def __init__(self, timer):
		self.timer = timer
		self.delays = []
		self.modifier = 0

		ExtScheduler().add_new_object(self.check_speed, self, 0.25, loops=-1)

	def end(self):
		ExtScheduler().rem_all_classinst_calls(self)

	def check_speed(self):
		"""Analyse recent delays and react by changing the game speed if need be"""
		if not self.delays:
			return
		old_mod = self.modifier
		avg_delay = sum(self.delays) / len(self.delays)
		major_delays = sum (1 for i in self.delays if i > Timer.ACCEPTABLE_TICK_DELAY)
		self.delays = []
		if avg_delay > self.__class__.AVG_DELAY_THRESHOLD:
			self._slow_down()
		else:
			self._speed_up()

		# slow down once for every 2 freeze protection triggers, but at most one complete step
		for i in xrange(min(major_delays/2, self.STEPS)):
			self._slow_down()

		print 'delay: ', avg_delay, ' new mod ', self.modifier, ' tps', self.get_actual_ticks_per_second(), ' major delays', major_delays

		if self.modifier != old_mod:
			GameSpeedChanged.broadcast(self, self.get_actual_ticks_per_second())

		# TODO: redraws on successive tick workoffs or stop the game (freeze protection)
		# TODO: only enable in sp games for now
		# TODO: suggest speed change to user possibly
		# TODO: fix game pause problems

	def _slow_down(self):
		if self.modifier >= self.__class__.STEPS:

			i = GAME_SPEED.TICK_RATES.index( self.timer.ticks_per_second )
			if i > 0:
				# TODO: do this in a nicer way in case we want this behaviour
				horizons.main._modules.session.speed_set( GAME_SPEED.TICK_RATES[i-1] )

			self.modifier /= 2 # don't change speed in very quick succession, but be aware that another change can be required soon

		else:
			self.modifier += 1

	def _speed_up(self):
		if self.modifier > 0:
			self.modifier -= 1


	def get_actual_ticks_per_second(self):
		ticks_per_second = self.timer.ticks_per_second
		if self.modifier == 0 or ticks_per_second == 0:
			return ticks_per_second
		else:
			# need to set the speed to a value between current speed and next slower value
			i = GAME_SPEED.TICK_RATES.index( ticks_per_second )
			if i > 0:
				lower_bound = GAME_SPEED.TICK_RATES[ i - 1 ]
			else:
				lower_bound = 2 # ticks per second

			interval = ticks_per_second - lower_bound
			mod = (float(interval) / self.STEPS) * self.modifier
			mod = int(mod)

			return ticks_per_second - mod
