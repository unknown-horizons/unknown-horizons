# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

import horizons.main
from horizons.util import WorldObject, Callback, ActionSetLoader
from horizons.gui.tabs import BuildRelatedTab

class ConcretObject(WorldObject):
	"""Class for concrete objects like Units or Buildings.
	"Concrete" here means "you can touch it", e.g. a Branch Office is a ConcreteObject,
	a Settlement isn't.
	All such objects have positions, so Islands are no ConcreteObjects for technical reasons.

	Assumes that object has a member _instance.
	"""
	movable = False # whether instance can move
	tabs = [] # iterable collection of classes of tabs to show when selected
	enemy_tabs = [] # same as tabs, but used when clicking on enemy's instances
	is_unit = False
	is_building = False
	is_selectable = False

	def __init__(self, session, **kwargs):
		"""
		@param session: Session instance this obj belongs to
		"""
		super(ConcretObject, self).__init__(**kwargs)
		self.session = session
		self.__init()

	def __init(self):
		self._instance = None # overwrite in subclass __init[__]
		self._action = 'idle' # Default action is idle
		self._action_set_id = self.session.db.get_random_action_set(self.id)[0]
		
		related_building = self.session.db.cached_query("SELECT building FROM related_buildings where building = ?", self.id)
		
		# if related_buildings found add the BuildRelatedTab
		if len(related_building) > 0:
			self.tabs += (BuildRelatedTab,)
		else:
			# if no related_buildings found, search for wrongly added BuildRelatedTabs
			# and delete them
			tabindex = 0
			for tab in self.tabs:
				if tab is BuildRelatedTab:
					del self.tabs[tabindex]
		
				tabindex += 1
		

	@property
	def fife_instance(self):
		return self._instance

	def save(self, db):
		super(ConcretObject, self).save(db)
		db("INSERT INTO concrete_object(id, action_runtime) VALUES(?, ?)", self.worldid, \
		   self._instance.getActionRuntime())

	def load(self, db, worldid):
		super(ConcretObject, self).load(db, worldid)
		self.__init()
		runtime = db.get_concrete_object_action_runtime(worldid)
		# delay setting of runtime until load of sub/super-class has set the action
		def set_action_runtime(self, runtime):
			# workaround to delay resolution of self._instance, which doesn't exist yet
			self._instance.setActionRuntime(runtime)
		Scheduler().add_new_object( Callback(set_action_runtime, self, runtime), self, run_in=0)

	def act(self, action, facing_loc=None, repeating=False):
		if facing_loc is None:
			facing_loc = self._instance.getFacingLocation()
		if not self.has_action(action):
			action = 'idle'
		self._instance.act(action+"_"+str(self._action_set_id), facing_loc, repeating)
		self._action = action

	def has_action(self, action):
		"""Checks if this unit has a certain action.
		@param anim: animation id as string"""
		return (action in ActionSetLoader.get_action_sets()[self._action_set_id])

	def remove(self):
		self._instance.getLocationRef().getLayer().deleteInstance(self._instance)
		self._instance = None
		Scheduler().rem_all_classinst_calls(self)
		super(ConcretObject, self).remove()

	def show_menu(self):
		"""Shows tabs from self.__class__.tabs, if there are any"""
		# this local import prevents circular imports
		from horizons.gui.tabs import TabWidget
		tablist = []
		if self.owner == self.session.world.player:
			tablist = self.tabs
		else: # this is an enemy instance with respect to the local player
			tablist = self.enemy_tabs

		if tablist:
			tabs = [ tabclass(self) for tabclass in tablist ]
			self.session.ingame_gui.show_menu(TabWidget(self.session.ingame_gui, \
			                                            tabs=tabs))

