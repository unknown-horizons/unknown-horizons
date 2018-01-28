# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

import random

from horizons.constants import ACTION_SETS
from horizons.messaging import ActionChanged
from horizons.scheduler import Scheduler
from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.util.python.callback import Callback
from horizons.util.worldobject import WorldObject
from horizons.world.units import UnitClass


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

	def __init__(self, session, action_set_id=None, **kwargs):
		"""
		@param session: Session instance this obj belongs to
		"""
		super().__init__(**kwargs)
		from horizons.session import Session
		assert isinstance(session, Session)
		self.session = session
		self.__init(action_set_id)

	def __init(self, action_set_id=None):
		# overwrite in subclass __init[__]
		self._instance = None
		# Default action is 'idle'
		self._action = 'idle'
		# NOTE: this can't be level-aware since not all ConcreteObjects have levels
		self._action_set_id = action_set_id if action_set_id else self.__class__.get_random_action_set()

		# only buildings for now
		# NOTE: this is player dependent, therefore there must be no calls to session.random that depend on this
		self.has_status_icon = self.is_building and self.show_status_icons and \
			self.owner is not None and self.owner.is_local_player # and only for the player's buildings

	@property
	def fife_instance(self):
		return self._instance

	def save(self, db):
		super().save(db)
		db("INSERT INTO concrete_object(id, action_runtime, action_set_id) VALUES(?, ?, ?)", self.worldid,
			 self._instance.getActionRuntime(), self._action_set_id)

	def load(self, db, worldid):
		super().load(db, worldid)
		runtime, action_set_id = db.get_concrete_object_data(worldid)
		# action_set_id should never be None in regular games,
		# but this information was lacking in savegames before rev 59.
		if action_set_id is None:
			action_set_id = self.__class__.get_random_action_set(level=self.level if hasattr(self, "level") else 0)
		self.__init(action_set_id)

		# delay setting of runtime until load of sub/super-class has set the action
		def set_action_runtime(self, runtime):
			# workaround to delay resolution of self._instance, which doesn't exist yet
			self._instance.setActionRuntime(runtime)
		Scheduler().add_new_object(Callback(set_action_runtime, self, runtime), self, run_in=0)

	def act(self, action, facing_loc=None, repeating=False, force_restart=True):
		"""
		@param repeating: maps to fife instance method actRepeat or actOnce
		@param force_restart: whether to always restart, even if action is already displayed
		"""
		if not self.has_action(action):
			action = 'idle'

		if not force_restart and self._action == action:
			return

		self._action = action

		# TODO This should not happen, this is a fix for the component introduction
		# Should be fixed as soon as we move concrete object to a component as well
		# which ensures proper initialization order for loading and initing
		if self._instance is None:
			return

		if facing_loc is None:
			facing_loc = self._instance.getFacingLocation()
		UnitClass.ensure_action_loaded(self._action_set_id, action) # lazy
		if repeating:
			self._instance.actRepeat(action + "_" + str(self._action_set_id), facing_loc)
		else:
			self._instance.actOnce(action + "_" + str(self._action_set_id), facing_loc)

	def has_action(self, action):
		"""Checks if this unit has a certain action.
		@param action: animation id as string"""
		return (action in ActionSetLoader.get_set(self._action_set_id))

	def remove(self):
		self._instance.getLocationRef().getLayer().deleteInstance(self._instance)
		self._instance = None
		Scheduler().rem_all_classinst_calls(self)
		super().remove()

	@classmethod
	def weighted_choice(cls, weighted_dict):
		""" http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python/
		"""
		# usually we do not need any magic because there only is one set:
		if len(weighted_dict) == 1:
			return list(weighted_dict.keys())[0]
		weights = sum(ACTION_SETS.DEFAULT_WEIGHT if w is None else w
		              for i, w in weighted_dict.items())
		rnd = random.random() * weights
		for action_set, weight in weighted_dict.items():
			rnd -= ACTION_SETS.DEFAULT_WEIGHT if weight is None else weight
			if rnd < 0:
				return action_set

	@classmethod
	def get_random_action_set(cls, level=0, exact_level=False):
		"""Returns an action set for an object of type object_id in a level <= the specified level.
		The highest level number is preferred.
		@param level: level to prefer. a lower level might be chosen
		@param exact_level: choose only action sets from this level. return val might be None here.
		@return: action_set_id or None"""
		action_sets = cls.action_sets
		action_set = None
		if exact_level:
			if level in action_sets:
				action_set = cls.weighted_choice(action_sets[level])
			# if there isn't one, stick with None
		else: # search all levels for an action set, starting with highest one
			for possible_level in reversed(range(level + 1)):
				if possible_level in (action_sets.keys()):
					action_set = cls.weighted_choice(action_sets[possible_level])
					break
			if action_set is None: # didn't find a suitable one
				# fall back to one from a higher level.
				# this does not happen in valid games, but can happen in tests, when level
				# constraints are ignored.
				action_set, weight = list(list(action_sets.values())[0].items())[0]

		return action_set

	@property
	def name(self):
		if hasattr(self, "_level_specific_names"):
			return self._level_specific_names[self.level]
		else:
			return self._name
