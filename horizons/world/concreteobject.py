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

from horizons.scheduler import Scheduler
from horizons.util import WorldObject, Callback, ActionSetLoader
from horizons.world.units import UnitClass
from random import randint

class ConcreteObject(WorldObject):
	"""Class for concrete objects like Units or Buildings.
	"Concrete" here means "you can touch it", e.g. a Warehouse is a ConcreteObject,
	a Settlement isn't.
	All such objects have positions, so Islands are no ConcreteObjects for technical reasons.

	Assumes that object has a member _instance.
	"""
	movable = False # whether instance can move
	is_unit = False
	is_building = False

	def __init__(self, session, **kwargs):
		"""
		@param session: Session instance this obj belongs to
		"""
		super(ConcreteObject, self).__init__(**kwargs)
		from horizons.session import Session
		assert isinstance(session, Session)
		self.session = session
		self.__init()

	def __init(self):
		self._instance = None # overwrite in subclass __init[__]
		self._action = 'idle' # Default action is idle
		self._action_set_id = self.get_random_action_set()[0]

		# only buildings for now
		# NOTE: this is player dependant, therefore there must be no calls to session.random that depend on this
		self.has_status_icon = self.is_building and \
		  not self.id in self.session.db.get_status_icon_exclusions() and \
			self.owner == self.session.world.player # and only for the player's buildings

	@property
	def fife_instance(self):
		return self._instance

	def save(self, db):
		super(ConcreteObject, self).save(db)
		db("INSERT INTO concrete_object(id, action_runtime) VALUES(?, ?)", self.worldid, \
			 self._instance.getActionRuntime())

	def load(self, db, worldid):
		super(ConcreteObject, self).load(db, worldid)
		self.__init()
		runtime = db.get_concrete_object_action_runtime(worldid)
		# delay setting of runtime until load of sub/super-class has set the action
		def set_action_runtime(self, runtime):
			# workaround to delay resolution of self._instance, which doesn't exist yet
			self._instance.setActionRuntime(runtime)
		Scheduler().add_new_object( Callback(set_action_runtime, self, runtime), self, run_in=0)

	def act(self, action, facing_loc=None, repeating=False):
		if not self.has_action(action):
			action = 'idle'
		# TODO This should not happen, this is a fix for the component introduction
		# Should be fixed as soon as we move concrete object to a component as well
		# which ensures proper initialization order for loading and initing
		if self._instance is not None:
			if facing_loc is None:
				facing_loc = self._instance.getFacingLocation()
			UnitClass.ensure_action_loaded(self._action_set_id, action) # lazy
			self._instance.act(action+"_"+str(self._action_set_id), facing_loc, repeating)
		self._action = action

	def has_action(self, action):
		"""Checks if this unit has a certain action.
		@param anim: animation id as string"""
		return (action in ActionSetLoader.get_sets()[self._action_set_id])

	def remove(self):
		self._instance.getLocationRef().getLayer().deleteInstance(self._instance)
		self._instance = None
		Scheduler().rem_all_classinst_calls(self)
		super(ConcreteObject, self).remove()

	@classmethod
	def get_random_action_set(cls, level=0, exact_level=False):
		"""Returns an action set for an object of type object_id in a level <= the specified level.
		The highest level number is preferred.
		@param db: UhDbAccessor
		@param object_id: type id of building
		@param level: level to prefer. a lower level might be chosen
		@param exact_level: choose only action sets from this level. return val might be None here.
		@return: tuple: (action_set_id, preview_action_set_id)"""
		assert level >= 0

		action_sets_by_lvl = cls.action_sets_by_level
		action_sets = cls.action_sets
		action_set = None
		preview = None
		if exact_level:
			action_set = action_sets_by_lvl[level][randint(0, len(action_sets_by_lvl[level])-1)] if len(action_sets_by_lvl[level]) > 0 else None
		else: # search all levels for an action set, starting with highest one
			for possible_level in reversed(xrange(level+1)):
				if len(action_sets_by_lvl[possible_level]) > 0:
					action_set = action_sets_by_lvl[possible_level][randint(0, len(action_sets_by_lvl[possible_level])-1)]
					break
			if action_set is None:
				assert False, "Couldn't find action set for obj %s(%s) in lvl %s" % (cls.id, cls.name, level)

		if action_set is not None and 'preview' in action_sets[action_set]:
			preview = action_sets[action_set]['preview']
		return (action_set, preview)

	@property
	def name(self):
		if hasattr(self, "_level_specific_names"):
			return self._level_specific_names[self.level]
		else:
			return self._name

