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

import operator
import logging
from collections import namedtuple

from horizons.scheduler import Scheduler

from horizons.util.pathfinding import PathBlockedError
from horizons.util import WorldObject, decorators, Callback
from horizons.ext.enum import Enum
from horizons.world.units.unit import Unit
from horizons.constants import COLLECTORS
from horizons.component.storagecomponent import StorageComponent
from horizons.component.restrictedpickup import RestrictedPickup
from horizons.component.ambientsoundcomponent import AmbientSoundComponent

class Collector(Unit):
	"""Base class for every collector. Does not depend on any home building.

	Timeline:
	 * search_job
	 * * get_job
	 * * handle_no_possible_job
	 * * begin_current_job
	 * * * setup_new_job
	 * * * move to target
	 on arrival there:
	 * begin_working
	 after some pretended working:
	 * finish_working
	 * * transfer_res
	 after subclass has done actions to finish job:
	 * end_job
	"""
	log = logging.getLogger("world.units.collector")

	work_duration = COLLECTORS.DEFAULT_WORK_DURATION # default is 16
	destination_always_in_building = False

	# all states, any (subclass) instance may have. Keeping a list in one place
	# is important, because every state must have a distinct number.
	# Handling of subclass specific states is done by subclass.
	states = Enum('idle', # doing nothing, waiting for job
	              'moving_to_target',
	              'working',
	              'moving_home',
	              'waiting_for_animal_to_stop', # herder: wait for job target to finish for collecting
	              'waiting_for_herder', # animal: has stopped, now waits for herder
	              'no_job_walking_randomly', # animal: like idle, but moving instead of standing still
	              'no_job_waiting', # animal: as idle, but no move target can be found
	              # TODO: merge no_job_waiting with idle
	              'decommissioned', # fisher ship: When home building got demolished. No more collecting.
	              )


	# INIT/DESTRUCT

	def __init__(self, x, y, slots=1, start_hidden=True, **kwargs):
		super(Collector, self).__init__(slots=slots,
		                                x=x, y=y,
		                                **kwargs)

		self.__init(self.states.idle, start_hidden)

		# start searching jobs just when construction (of subclass) is completed
		Scheduler().add_new_object(self.search_job, self, 1)

	def __init(self, state, start_hidden):
		self.state = state
		self.start_hidden = start_hidden
		if self.start_hidden:
			self.hide()

		self.job = None # here we store the current job as Job object

	def remove(self):
		"""Removes the instance. Useful when the home building is destroyed"""
		self.log.debug("%s: remove called", self)
		self.cancel(continue_action=lambda : 42)
		# remove from target collector list
		if self.job is not None and self.state != self.states.moving_home:
			# in the move_home state, there still is a job, but the collector is already deregistered
			self.job.object.remove_incoming_collector(self)
		self.hide()
		self.job = None
		super(Collector, self).remove()


	# SAVE/LOAD

	def save(self, db):
		super(Collector, self).save(db)

		# save state and remaining ticks for next callback
		# retrieve remaining ticks according current callback according to state
		current_callback = None
		remaining_ticks = None
		if self.state == self.states.idle:
			current_callback = self.search_job
		elif self.state == self.states.working:
			current_callback = self.finish_working
		if current_callback is not None:
			calls = Scheduler().get_classinst_calls(self, current_callback)
			assert len(calls) == 1, 'Collector should have callback %s scheduled, but has %s' % \
			        (current_callback, [ str(i) for i in Scheduler().get_classinst_calls(self).keys() ])
			remaining_ticks = max(calls.values()[0], 1) # save a number > 0

		db("INSERT INTO collector(rowid, state, remaining_ticks, start_hidden) VALUES(?, ?, ?, ?)",
		   self.worldid, self.state.index, remaining_ticks, self.start_hidden)

		# save the job
		if self.job is not None:
			obj_id = -1 if self.job.object is None else self.job.object.worldid
			# this is not in 3rd normal form since the object is saved multiple times but
			# it preserves compatiblity with old savegames this way.
			for entry in self.job.reslist:
				db("INSERT INTO collector_job(collector, object, resource, amount) VALUES(?, ?, ?, ?)",
				   self.worldid, obj_id, entry.res, entry.amount)

	def load(self, db, worldid):
		super(Collector, self).load(db, worldid)

		# load collector properties
		state_id, remaining_ticks, start_hidden = \
		        db("SELECT state, remaining_ticks, start_hidden FROM collector \
		            WHERE rowid = ?", worldid)[0]
		self.__init(self.states[state_id], start_hidden)

		# load job
		job_db = db("SELECT object, resource, amount FROM collector_job WHERE collector = ?", worldid)
		if job_db:
			reslist = []
			for obj, res, amount in job_db:
				reslist.append( Job.ResListEntry(res, amount, False) )
			# create job with worldid of object as object. This is used to defer the target resolution,
			# which might not have been loaded
			self.job = Job(obj, reslist)

		def fix_job_object():
			# resolve worldid to object later
			if self.job:
				if self.job.object == -1:
					self.job.object = None
				else:
					self.job.object = WorldObject.get_object_by_id( self.job.object )

		# apply state when job object is loaded for sure
		Scheduler().add_new_object(
		  Callback.ChainedCallbacks(
		    fix_job_object,
		  	Callback(self.apply_state, self.state, remaining_ticks)),
		    self, run_in=0
		)

	def apply_state(self, state, remaining_ticks=None):
		"""Takes actions to set collector to a state. Useful after loading.
		@param state: EnumValue from states
		@param remaining_ticks: ticks after which current state is finished
		"""
		if state == self.states.idle:
			# we do nothing, so schedule a new search for a job
			Scheduler().add_new_object(self.search_job, self, remaining_ticks)
		elif state == self.states.moving_to_target:
			# we are on the way to target, so save the job
			self.setup_new_job()
			# and notify us, when we're at target
			self.add_move_callback(self.begin_working)
			self.add_blocked_callback(self.handle_path_to_job_blocked)
			self.show()
		elif state == self.states.working:
			# we are at the target and work
			# register the new job
			self.setup_new_job()
			# job finishes in remaining_ticks ticks
			Scheduler().add_new_object(self.finish_working, self, remaining_ticks)


	# GETTER

	def get_home_inventory(self):
		"""Returns inventory where collected res will be stored.
		This could be the inventory of a home_building, or it's own.
		"""
		raise NotImplementedError

	def get_colleague_collectors(self):
		"""Returns a list of collectors, that work for the same "inventory"."""
		return []

	def get_collectable_res(self):
		"""Return all resources the collector can collect"""
		raise NotImplementedError

	def get_job(self):
		"""Returns the next job or None"""
		raise NotImplementedError


	# BEHAVIOUR
	def search_job(self):
		"""Search for a job, only called if the collector does not have a job.
		If no job is found, a new search will be scheduled in a few ticks."""
		self.job = self.get_job()
		if self.job is None:
			self.handle_no_possible_job()
		else:
			self.begin_current_job()

	def handle_no_possible_job(self):
		"""Called when we can't find a job. default is to wait and try again in a few secs"""
		self.log.debug("%s: found no possible job, retry in %s ticks", self, COLLECTORS.DEFAULT_WAIT_TICKS)
		Scheduler().add_new_object(self.search_job, self, COLLECTORS.DEFAULT_WAIT_TICKS)

	def setup_new_job(self):
		"""Executes the necessary actions to begin a new job"""
		self.job.object.add_incoming_collector(self)

	def check_possible_job_target(self, target):
		"""Checks our if we "are allowed" and able to pick up from the target"""
		# Discard building if it works for same inventory (happens when both are storage buildings
		# or home_building is checked out)
		if target.get_component(StorageComponent).inventory is self.get_home_inventory():
			#self.log.debug("nojob: same inventory")
			return False

		if self.has_component(RestrictedPickup): # check if we're allowed to pick up there
			return self.get_component(RestrictedPickup).pickup_allowed_at(target.id)

		# pathfinding would fit in here, but it's too expensive,
		# we just do that at targets where we are sure to get a lot of res later on.

		return True

	@decorators.make_constants()
	def check_possible_job_target_for(self, target, res):
		"""Checks out if we could get res from target.
		Does _not_ check for anything else (e.g. if we are able to walk there).
		@param target: possible target. buildings are supported, support for more can be added.
		@param res: resource id
		@return: instance of Job or None, if we can't collect anything
		"""
		res_amount = target.get_available_pickup_amount(res, self)
		if res_amount <= 0:
			#self.log.debug("nojob: no pickup amount")
			return None

		# check if other collectors get this resource, because our inventory could
		# get full if they arrive.
		total_registered_amount_consumer = sum(
		  entry.amount for
		  collector in self.get_colleague_collectors() if
		  collector.job is not None for
		  entry in collector.job.reslist if
		  entry.res == res )

		inventory = self.get_home_inventory()

		# check if there are resources left to pickup
		home_inventory_free_space = inventory.get_limit(res) - \
		                        (total_registered_amount_consumer + inventory[res])
		if home_inventory_free_space <= 0:
			#self.log.debug("nojob: no home inventory space")
			return None

		collector_inventory_free_space = self.get_component(StorageComponent).inventory.get_free_space_for(res)
		if collector_inventory_free_space <= 0:
			#self.log.debug("nojob: no collector inventory space")
			return None

		possible_res_amount = min(res_amount, home_inventory_free_space,
		                          collector_inventory_free_space)

		target_inventory_full = (target.get_component(StorageComponent).inventory.get_free_space_for(res) == 0)

		# create a new data line.
		return Job.ResListEntry(res, possible_res_amount, target_inventory_full)

	def get_best_possible_job(self, jobs):
		"""Return best possible job from jobs.
		"Best" means that the job is highest when the job list was sorted.
		"Possible" means that we can find a path there.
		@param jobs: unsorted JobList instance
		@return: selected Job instance from list or None if no jobs are possible."""
		jobs.sort_jobs()
		# check if we can move to that targets
		for job in jobs:
			path = self.check_move(job.object.loading_area)
			if path:
				job.path = path
				return job

		return None

	def begin_current_job(self, job_location=None):
		"""Starts executing the current job by registering itself and moving to target.
		@param job_location: Where collector should work. default: job.object.loading_area"""
		self.log.debug("%s prepares job %s", self, self.job)
		self.setup_new_job()
		self.show()
		if job_location is None:
			job_location = self.job.object.loading_area
		self.move(job_location, self.begin_working,
		          destination_in_building = self.destination_always_in_building,
		          blocked_callback = self.handle_path_to_job_blocked, path=self.job.path)
		self.state = self.states.moving_to_target

	def resume_movement(self):
		"""Try to resume movement after getting blocked. If that fails then wait and try again."""
		try:
			self._move_tick(resume=True)
		except PathBlockedError:
			Scheduler().add_new_object(self.resume_movement, self, COLLECTORS.DEFAULT_WAIT_TICKS)

	def handle_path_to_job_blocked(self):
		"""Called when we get blocked while trying to move to the job location.
		The default action is to resume movement in a few seconds."""
		self.log.debug("%s: got blocked while moving to the job location, trying again in %s ticks.",
			self, COLLECTORS.DEFAULT_WAIT_TICKS)
		Scheduler().add_new_object(self.resume_movement, self, COLLECTORS.DEFAULT_WAIT_TICKS)

	def begin_working(self):
		"""Pretends that the collector works by waiting some time. finish_working is
		called after that time."""
		self.log.debug("%s begins working", self)
		assert self.job is not None, '%s job is None in begin_working' % self
		Scheduler().add_new_object(self.finish_working, self, self.work_duration)
		# play working sound
		if self.has_component(AmbientSoundComponent):
			am_comp = self.get_component(AmbientSoundComponent)
			if am_comp.soundfiles:
				am_comp.play_ambient(am_comp.soundfiles[0], position=self.position)
		self.state = self.states.working

	def finish_working(self):
		"""Called when collector has stayed at the target for a while.
		Picks up the resources.
		Should be overridden to specify what the collector should do after this."""
		self.log.debug("%s finished working", self)
		self.act("idle", self._instance.getFacingLocation(), True)
		# deregister at the target we're at
		self.job.object.remove_incoming_collector(self)
		# reconsider job now: there might now be more res available than there were when we started

		reslist = ( self.check_possible_job_target_for(self.job.object, res) for res in self.get_collectable_res() )
		reslist = [i for i in reslist if i]
		if reslist:
			self.job.reslist = reslist

		# transfer res (this must be the last step, it will trigger consecutive actions through the
		# target inventory changelistener, and the collector must be in a consistent state then.
		self.transfer_res_from_target()
		# stop playing ambient sound if any
		if self.has_component(AmbientSoundComponent):
			self.get_component(AmbientSoundComponent).stop_sound()

	def transfer_res_from_target(self):
		"""Transfers resources from target to collector inventory"""
		new_reslist = []
		for entry in self.job.reslist:
			actual_amount = self.job.object.pickup_resources(entry.res, entry.amount, self)
			if entry.amount != actual_amount:
				new_reslist.append( Job.ResListEntry(entry.res, actual_amount, False) )
			else:
				new_reslist.append( entry )

			remnant = self.get_component(StorageComponent).inventory.alter(entry.res, actual_amount)
			assert remnant == 0, "%s couldn't take all of res %s; remnant: %s; planned: %s" % \
				     (self, entry.res, remnant, entry.amount)
		self.job.reslist = new_reslist

	def transfer_res_to_home(self, res, amount):
		"""Transfer resources from collector to the home inventory"""
		self.log.debug("%s brought home %s of %s", self, amount, res)
		remnant = self.get_home_inventory().alter(res, amount)
		#assert remnant == 0, "Home building could not take all resources from collector."
		remnant = self.get_component(StorageComponent).inventory.alter(res, -amount)
		assert remnant == 0, "%s couldn't give all of res %s; remnant: %s; inventory: %s" % \
		       (self, res, remnant, self.get_component(StorageComponent).inventory)

	# unused reroute code removed in 2aef7bba77536da333360566467d9a2f08d38cab

	def end_job(self):
		"""Contrary to setup_new_job"""
		# the job now is finished now
		# before the new job can begin this will be executed
		self.log.debug("%s end_job - waiting for new search_job", self)
		if self.start_hidden:
			self.hide()
		self.job = None
		Scheduler().add_new_object(self.search_job , self, COLLECTORS.DEFAULT_WAIT_TICKS)
		self.state = self.states.idle

	def cancel(self, continue_action):
		"""Aborts the current job.
		@param continue_action: Callback, gets called after cancel. Specifies what collector
			                      is supposed to now.
		NOTE: Subclasses set this to a proper action that makes the collector continue to work.
		      If the collector is supposed to be remove, use a noop.
		"""
		self.stop()
		self.log.debug("%s was canceled, continue action is %s", self, continue_action)
		if self.job is not None:
			# remove us as incoming collector at target
			if self.state != self.states.moving_home:
				# in the moving_home state, the job object still exists,
				# but the collector is already deregistered
				self.job.object.remove_incoming_collector(self)
			# clean up depending on state
			if self.state == self.states.working:
				removed_calls = Scheduler().rem_call(self, self.finish_working)
				assert removed_calls == 1, 'removed %s calls instead of one' % removed_calls
			self.job = None
			self.state = self.states.idle
		# NOTE:
		# Some blocked movement callbacks use this callback. All blocked movement callbacks have to
		# be canceled here, else the unit will try to continue the movement later when its state has already changed.
		# This line should fix it sufficiently for now and the problem could be deprecated when the
		# switch to a component-based system is accomplished.
		Scheduler().rem_call(self, self.resume_movement)
		continue_action()

	def __str__(self):
		try:
			return super(Collector, self).__str__() + "(state=%s)" % self.state
		except AttributeError: # state has not been set
			return super(Collector, self).__str__()


class Job(object):
	"""Data structure for storing information of collector jobs"""
	ResListEntry = namedtuple("ResListEntry", ["res", "amount", "target_inventory_full"])
	def __init__(self, obj, reslist):
		"""
		@param obj: ResourceHandler that provides res
		@param reslist: ResListEntry list
			res: resource to get
			amount: amount of resource to get
			target_inventory_full: whether target inventory can't store any more of this res.
		"""
		for entry in reslist:
			assert entry.amount >= 0
		# can't assert that it's not 0, since the value is reset to the amount
		# the collector actually got at the target, which might be 0. yet for new jobs
		# amount > 0 is a necessary precondition.

		self.object = obj
		self.reslist = reslist

		self.path = None # attribute to temporarily store path

	@decorators.cachedproperty
	def amount_sum(self):
		# NOTE: only guaranteed to be correct during job search phase
		return sum(entry.amount for entry in self.reslist)

	@decorators.cachedproperty
	def resources(self):
		# NOTE: only guaranteed to be correct during job search phase
		return [entry.res for entry in self.reslist]

	@decorators.cachedproperty
	def target_inventory_full_num(self):
		# NOTE: only guaranteed to be correct during job search phase
		return sum(1 for entry in self.reslist if entry.target_inventory_full)

	def __str__(self):
		return "Job(%s, %s)" % (self.object, self.reslist)


class JobList(list):
	"""Data structure for evaluating best jobs.
	It's a list extended by special sort functions.
	"""
	order_by = Enum('rating', 'amount', 'random', 'fewest_available', 'fewest_available_and_distance', 'for_storage_collector', 'distance')

	def __init__(self, collector, job_order):
		"""
		@param collector: collector instance
		@param job_order: instance of order_by-Enum
		"""
		super(JobList, self).__init__()
		self.collector = collector
		# choose acctual function by name of enum value
		sort_fun_name = '_sort_jobs_' + str(job_order)
		if not hasattr(self, sort_fun_name):
			self.sort_jobs = self._sort_jobs_amount
			print 'WARNING: invalid job order: ', job_order
		else:
			self.sort_jobs = getattr(self, sort_fun_name)

	def sort_jobs(self, obj):
		"""Call this to sort jobs"""
		# (this is overwritten in __init__)
		raise NotImplementedError

	def _sort_jobs_random(self):
		"""Sorts jobs randomly"""
		self.collector.session.random.shuffle(self)

	def _sort_jobs_amount(self):
		"""Sorts the jobs by the amount of resources available"""
		self.sort(key=operator.attrgetter('amount_sum'), reverse=True)

	def _sort_jobs_fewest_available(self, shuffle_first=True):
		"""Prefer jobs where least amount is available in obj's inventory.
		Only considers resource of resource list with minimum amount available.
		This is supposed to fix urgent shortages."""
		# shuffle list before sorting, so that jobs with same value have equal chance
		if shuffle_first:
			self.collector.session.random.shuffle(self)
		inventory = self.collector.get_home_inventory()
		self.sort(key=lambda job: min(inventory[res] for res in job.resources) , reverse=False)

	def _sort_jobs_fewest_available_and_distance(self):
		"""Sort jobs by fewest available, but secondaryly also consider distance"""
		# python sort is stable, so two sequenced sorts work.
		self._sort_jobs_distance()
		self._sort_jobs_fewest_available(shuffle_first=False)

	def _sort_jobs_for_storage_collector(self):
		"""Special sophisticated sorting routing for storage collectors.
		Same as fewest_available_and_distance_, but also considers whether target inv is full."""
		self._sort_jobs_fewest_available_and_distance()
		self._sort_target_inventory_full()

	def _sort_jobs_distance(self):
		"""Prefer targets that are nearer"""
		self.sort(key=lambda job: self.collector.position.distance(job.object.loading_area))

	def _sort_target_inventory_full(self):
		"""Prefer targets with full inventory"""
		self.sort(key=operator.attrgetter('target_inventory_full_num'), reverse=True)

	def __str__(self):
		return str([ str(i) for i in self ])


decorators.bind_all(Collector)
