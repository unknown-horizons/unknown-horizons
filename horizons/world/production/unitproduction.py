# -*- coding: utf-8 -*-
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

from horizons.world.production.production import ChangingProduction
from horizons.constants import PRODUCTION, RES
from horizons.scheduler import Scheduler

class UnitProduction(ChangingProduction):
	"""Production, that produces units."""
	USES_GOLD = True
	def __init__(self, load=False, **kwargs):
		super(UnitProduction, self).__init__(auto_start=False, load=load, **kwargs)
		if not load:
			self.__init()
			# We have to check manually now after initing because we set auto_start to false
			self._check_inventory()

	def __init(self):
		self.original_prod_line = self._prod_line.get_original_copy()

	def load(self, db, worldid):
		super(UnitProduction, self).load(db, worldid)
		self.__init()

	@property
	def progress(self):
		still_needed =  sum(self._prod_line.consumed_res.itervalues())
		all_needed = sum([amount for res, amount in self.original_prod_line.consumed_res.iteritems() if res != RES.GOLD_ID])
		return 1 - float(still_needed) / all_needed

	## PROTECTED METHODS
	def _get_producing_callback(self):
		return self._produce

	def _check_available_res(self):
		# Gold must be available from the beginning
		if self._prod_line.consumed_res.get(RES.GOLD_ID, 0) > 0: # check if gold is needed
			amount = self._prod_line.consumed_res[RES.GOLD_ID]
		for res, amount in self._prod_line.consumed_res.iteritems():
			# we change the production, so the amount can become 0
			# in this case, we must no consider this resource, as it has already been fully provided
			if amount == 0:
				continue # nothing to take here
			if res == RES.GOLD_ID:
				if self.owner_inventory[RES.GOLD_ID] > 0:
					return True
			elif self.inventory[res] > 0:
				return True
		return False

	def _remove_res_to_expend(self, return_without_gold=False):
		"""Takes as many res as there are and returns sum of amount of res taken.
		@param return_without_gold: return not an integer but a tuple, where the second value is without gold"""
		taken = 0
		taken_without_gold = 0
		for res, amount in self._prod_line.consumed_res.iteritems():
			if res == RES.GOLD_ID:
				inventory = self.owner_inventory
			else:
				inventory = self.inventory
			remnant = inventory.alter(res, amount) # try to get all
			self._prod_line.change_amount(res, remnant) # set how much we still need to get
			if return_without_gold and res != RES.GOLD_ID:
				taken_without_gold += abs(remnant) + amount
			taken += abs(remnant) + amount
		if return_without_gold:
			return (taken, taken_without_gold)
		else:
			return taken

	def _produce(self):
		# check if we're done
		still_needed_res = sum(self._prod_line.consumed_res.itervalues())
		if still_needed_res == 0:
			self._finished_producing()
			return

		removed_res, removed_res_without_gold = self._remove_res_to_expend(return_without_gold=True)
		# check if there were res
		if removed_res == 0:
			# watch inventory for new res
			self.inventory.add_change_listener(self._check_inventory)
			if self.__class__.USES_GOLD:
				self.owner_inventory.add_change_listener(self._check_inventory)
			self._state = PRODUCTION.STATES.waiting_for_res
			self._changed()
			return

		# calculate how much of the whole production process we can produce now
		# and set the scheduler waiting time accordingly (e.g. half of res => wait half of prod time)
		all_needed_res = sum( i[1] for i in self.original_prod_line.consumed_res.iteritems() if i[0] != RES.GOLD_ID )
		part_of_whole_production = float(removed_res_without_gold) / all_needed_res
		prod_time = Scheduler().get_ticks( part_of_whole_production * self._prod_line.time )
		prod_time = max(prod_time, 1) # wait at least 1 tick
		# do part of production and call this again when done
		Scheduler().add_new_object(self._produce, self, prod_time)


	def _finished_producing(self, **kwargs):
		super(UnitProduction, self)._finished_producing(continue_producing=False, **kwargs)
		self.state = PRODUCTION.STATES.done
		# reset prodline
		self._prod_line = self._prod_line.get_original_copy()
