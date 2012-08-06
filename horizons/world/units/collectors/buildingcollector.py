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

import weakref
from collections import deque

from horizons.util import WorldObject, RadiusRect, Callback, decorators
from horizons.util.pathfinding.pather import RoadPather, BuildingCollectorPather
from horizons.constants import COLLECTORS, BUILDINGS
from horizons.scheduler import Scheduler
from horizons.world.units.movingobject import MoveNotPossible
from horizons.world.units.collectors.collector import Collector, JobList, Job
from horizons.component.storagecomponent import StorageComponent
from horizons.component.collectingcomponent import CollectingComponent



class BuildingCollector(Collector):
	"""Collector, that works for a building and gets its needed resources.
	Essentially extends the Collector by a home building.

	Nearly all of the time, the collector has to has a home_building.
	Only fisher ships violate this rule in case their home building get's demolished.
	Therefore, this class is not functional with home_building == None,
	but basic facilities (esp. save/load) have to work.
	"""
	job_ordering = JobList.order_by.fewest_available_and_distance
	pather_class = BuildingCollectorPather

	def __init__(self, home_building, **kwargs):
		kwargs['x'] = home_building.position.origin.x
		kwargs['y'] = home_building.position.origin.y
		super(BuildingCollector, self).__init__(**kwargs)
		self._job_history = deque()
		self._creation_tick = Scheduler().cur_tick + 1 # adjusted for the initial delay
		self.__init(home_building)

	def __init(self, home_building):
		self.home_building = home_building
		if home_building is not None:
			self.register_at_home_building()
		# save whether it's possible for this instance to access a target
		# @chachedmethod is not applicable since it stores hard refs in the arguments
		self._target_possible_cache = weakref.WeakKeyDictionary()

	def save(self, db):
		super(BuildingCollector, self).save(db)
		self._clean_job_history_log()
		current_tick = Scheduler().cur_tick

		# save home_building and creation tick
		translated_creation_tick = self._creation_tick - current_tick + 1 #  pre-translate the tick number for the loading process
		db("INSERT INTO building_collector(rowid, home_building, creation_tick) VALUES(?, ?, ?)",
			 self.worldid, self.home_building.worldid if self.home_building is not None else None, translated_creation_tick)

		# save job history
		for tick, utilisation in self._job_history:
				# pre-translate the tick number for the loading process
			translated_tick = tick - current_tick + Scheduler.FIRST_TICK_ID
			db("INSERT INTO building_collector_job_history(collector, tick, utilisation) VALUES(?, ?, ?)",
				 self.worldid, translated_tick, utilisation)

	def load(self, db, worldid):
		# we have to call __init here before super().load, because a superclass uses a method,
		# which is overwritten here, that uses a member, which has to be initialised via __init.

		# load home_building
		home_building_id, self._creation_tick = db.get_building_collectors_data(worldid)
		self.__init(None if home_building_id is None else WorldObject.get_object_by_id(home_building_id))

		super(BuildingCollector, self).load(db, worldid)

		if home_building_id is None:
			self.show() # make sure that homebuildingsless units are visible on startup
			# TODO: fix "homebuildingless buildingcollectors".
			#       perhaps a new unit should be created, because a fisher ship without a
			#       fisher basically isn't a buildingcollector anymore.

		# load job search failures
		# the tick values were translated to assume that it is currently tick -1
		assert Scheduler().cur_tick == Scheduler.FIRST_TICK_ID - 1
		self._job_history = db.get_building_collector_job_history(worldid)

	def register_at_home_building(self, unregister=False):
		"""Creates reference for self at home building (only hard reference except for
		in job.object)
		@param unregister: whether to reverse registration
		"""
		# TODO: figure out why the home_building can be None when this is run in session.end()
		if self.home_building is not None:
			if unregister:
				self.home_building.get_component(CollectingComponent).remove_local_collector(self)
			else:
				self.home_building.get_component(CollectingComponent).add_local_collector(self)

	def apply_state(self, state, remaining_ticks=None):
		super(BuildingCollector, self).apply_state(state, remaining_ticks)
		if state == self.states.moving_home:
			# collector is on its way home
			self.add_move_callback(self.reached_home)
			self.add_blocked_callback(self.handle_path_home_blocked)
			self.show()

	def remove(self):
		self.register_at_home_building(unregister=True)
		self.home_building = None
		super(BuildingCollector, self).remove()

	def decouple_from_home_building(self):
		"""Makes collector survive deletion of home building."""
		self.cancel(continue_action=lambda : 42) # don't continue
		self.stop()
		self.register_at_home_building(unregister=True)
		self.home_building = None
		self.state = self.states.decommissioned
		self.show() # make sure collector is not pretending to be inside somewhere

	def get_home_inventory(self):
		return self.home_building.get_component(StorageComponent).inventory

	def get_colleague_collectors(self):
		colls = self.home_building.get_component(CollectingComponent).get_local_collectors()
		return ( coll for coll in colls if coll is not self )

	@decorators.make_constants()
	def get_job(self):
		"""Returns the next job or None"""
		if self.home_building is None:
			return None

		collectable_res = self.get_collectable_res()
		if not collectable_res:
			return None

		jobs = JobList(self, self.job_ordering)
		# iterate all building that provide one of the resources
		for building in self.get_buildings_in_range(reslist=collectable_res):
			# check if we can pickup here on principle
			target_possible = self._target_possible_cache.get(building, None)
			if target_possible is None: # not in cache, we have to check
				target_possible = self.check_possible_job_target(building)
				self._target_possible_cache[building] = target_possible

			if target_possible:
				# check for res here
				reslist = ( self.check_possible_job_target_for(building, res) for res in collectable_res )
				reslist = [i for i in reslist if i]

				if reslist: # we can do something here
					jobs.append( Job(building, reslist) )

		# TODO: find out why order of  self.get_buildings_in_range(..) and therefore order of jobs differs from client to client
		# TODO: find out why WildAnimal.get_job(..) doesn't have this problem
		# for MP-Games the jobs must have the same ordering to ensure get_best_possible_job(..) returns the same result
		jobs.sort(key=lambda job: job.object.worldid)

		return self.get_best_possible_job(jobs)

	def search_job(self):
		self._clean_job_history_log()
		super(BuildingCollector, self).search_job()

	def _clean_job_history_log(self):
		""" remove too old entries """
		first_relevant_tick = Scheduler().cur_tick - self.get_utilisation_history_length()
		while len(self._job_history) > 1 and self._job_history[1][0] < first_relevant_tick:
			self._job_history.popleft()

	def handle_no_possible_job(self):
		super(BuildingCollector, self).handle_no_possible_job()
		# only append a new element if it is different from the last one
		if not self._job_history or abs(self._job_history[-1][1]) > 1e-9:
			self._job_history.append((Scheduler().cur_tick, 0))

	def begin_current_job(self, job_location=None):
		super(BuildingCollector, self).begin_current_job(job_location)

		"""
		TODO: port to multiple resources and document this
		max_amount = min(self.get_component(StorageComponent).inventory.get_limit(self.job.res), self.job.object.get_component(StorageComponent).inventory.get_limit(self.job.res))
		utilisation = self.job.amount / float(max_amount)
		# only append a new element if it is different from the last one
		if not self._job_history or abs(self._job_history[-1][1] - utilisation) > 1e-9:
			self._job_history.append((Scheduler().cur_tick, utilisation))
		"""

	def finish_working(self, collector_already_home=False):
		"""Called when collector has stayed at the target for a while.
		Picks up the resources and sends collector home.
		@param collector_already_home: whether collector has moved home before."""
		if not collector_already_home:
			self.move_home(callback=self.reached_home)
		super(BuildingCollector, self).finish_working()

	# unused reroute code removed in 2aef7bba77536da333360566467d9a2f08d38cab

	def reached_home(self):
		"""Exchanges resources with home and calls end_job"""
		self.log.debug("%s reached home", self)
		for entry in self.job.reslist:
			self.transfer_res_to_home(entry.res, entry.amount)
		self.end_job()

	def get_collectable_res(self):
		"""Return all resources the collector can collect (depends on its home building)"""
		# find needed res (only res that we have free room for) - Building function
		return self.home_building.get_needed_resources()

	def get_buildings_in_range(self, reslist=None):
		"""Returns all buildings in range .
		Overwrite in subclasses that need ranges around the pickup.
		@param res: optional, only search for buildings that provide res"""
		reach = RadiusRect(self.home_building.position, self.home_building.radius)
		return self.home_building.island.get_providers_in_range(reach, reslist=reslist,
								                                            player=self.owner)

	def handle_path_home_blocked(self):
		"""Called when we get blocked while trying to move to the job location. """
		self.log.debug("%s: got blocked while moving home, teleporting home", self)
		# make sure to get home, this prevents all movement problems by design
		# at the expense of some jumping in very unusual corner cases
		# NOTE: if this is seen as problem, self.resume_movement() could be tried before reverting to teleportation
		self.teleport(self.home_building, callback=self.move_callbacks, destination_in_building=True)

	def move_home(self, callback=None, action='move_full'):
		"""Moves collector back to its home building"""
		self.log.debug("%s move_home", self)
		if self.home_building.position.contains(self.position):
			# already home
			self.stop() # make sure unit doesn't go anywhere in case a movement is going on
			Scheduler().add_new_object(callback, self, run_in=0)
		else:
			# actually move home
			try:
				# reuse reversed path of path here (assumes all jobs started at home)
				path = None if (self.job is None or self.job.path is None) else list(reversed(self.job.path))
				self.move(self.home_building, callback=callback, destination_in_building=True,
				          action=action, blocked_callback=self.handle_path_home_blocked, path=path)
				self.state = self.states.moving_home
			except MoveNotPossible:
				# we are in trouble.
				# the collector went somewhere, now there is no way for them to move home.
				# this is an unsolved problem also in reality, so we are forced to use an unconventional solution.
				self.teleport(self.home_building, callback=callback, destination_in_building=True)

	def cancel(self, continue_action=None):
		"""Cancels current job and moves back home"""
		self.log.debug("%s cancel", self)
		if continue_action is None:
			continue_action = Callback(self.move_home, callback=self.end_job, action='move')
		super(BuildingCollector, self).cancel(continue_action=continue_action)

	def get_utilisation_history_length(self):
		return min(COLLECTORS.STATISTICAL_WINDOW, Scheduler().cur_tick - self._creation_tick)

	def get_utilisation(self):
		"""
		Returns the utilisation of the collector.
		It is calculated by observing how full the inventory of the collector is or
		how full it would be if it had reached the place where it picks up the resources.
		"""

		history_length = self.get_utilisation_history_length()
		if history_length <= 0:
			return 0

		current_tick = Scheduler().cur_tick
		first_relevant_tick = current_tick - history_length

		self._clean_job_history_log()
		num_entries = len(self._job_history)
		total_utilisation = 0
		for i in xrange(num_entries):
			tick = self._job_history[i][0]
			if tick >= current_tick:
				break

			next_tick = min(self._job_history[i + 1][0], current_tick) if i + 1 < num_entries else current_tick
			relevant_ticks = next_tick - tick
			if tick < first_relevant_tick:
				# the beginning is not relevant
				relevant_ticks -= first_relevant_tick - tick
			total_utilisation += relevant_ticks * self._job_history[i][1]

		#assert -1e-7 < total_utilisation / float(history_length) < 1 + 1e-7
		return total_utilisation / float(history_length)

class StorageCollector(BuildingCollector):
	""" Same as BuildingCollector, except that it moves on roads.
	Used in storage facilities.
	"""
	pather_class = RoadPather
	destination_always_in_building = True
	job_ordering = JobList.order_by.for_storage_collector

class FieldCollector(BuildingCollector):
	""" Similar to the BuildingCollector but used on farms for example.
	The main difference is that it uses a different way to sort it's jobs, to make for a nicer
	look of farm using."""
	job_ordering = JobList.order_by.random

class SettlerCollector(StorageCollector):
	"""Collector for settlers."""
	pass

class FisherShipCollector(BuildingCollector):

	def __init__(self, *args, **kwargs):
		if not args:
			# We haven't preset a home_building, so search for one!
			home_building = self.get_smallest_fisher(kwargs['session'], kwargs['owner'])
			super(FisherShipCollector, self).__init__(home_building=home_building, *args, **kwargs)
		else:
			super(FisherShipCollector, self).__init__(*args, **kwargs)

	def get_smallest_fisher(self, session, owner):
		"""Returns the fisher with the least amount of boats"""
		fishers = []
		for settlement in session.world.settlements:
			if settlement.owner == owner:
				fishers.extend(settlement.buildings_by_id[BUILDINGS.FISHER])
		smallest_fisher = fishers.pop()
		for fisher in fishers:
			if len(smallest_fisher.get_local_collectors()) > len(fisher.get_local_collectors()):
				smallest_fisher = fisher

		return smallest_fisher

	def get_buildings_in_range(self, reslist=None):
		"""Returns all buildings in range .
		Overwrite in subclasses that need ranges around the pickup.
		@param res: optional, only search for buildings that provide res"""
		reach = RadiusRect(self.home_building.position, self.home_building.radius)
		return self.session.world.get_providers_in_range(reach, reslist=reslist)

class DisasterRecoveryCollector(StorageCollector):
	"""Collects disasters such as fire or pestilence."""
	def finish_working(self, collector_already_home=False):
		super(DisasterRecoveryCollector, self).finish_working(collector_already_home=collector_already_home)
		building = self.job.object
		if hasattr(building, "disaster"): # make sure that building hasn't recovered any other way
			building.disaster.recover(building)

	def get_job(self):
		if self.home_building is not None and \
		   not self.session.world.disaster_manager.is_affected( self.home_building.settlement ):
			return None # not one disaster active, bail out

		return super(DisasterRecoveryCollector, self).get_job()

decorators.bind_all(BuildingCollector)
decorators.bind_all(FieldCollector)
decorators.bind_all(FisherShipCollector)
decorators.bind_all(SettlerCollector)
decorators.bind_all(StorageCollector)
decorators.bind_all(DisasterRecoveryCollector)
