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

import logging

from fife import fife

from horizons.command.building import Build
from horizons.component.collectingcomponent import CollectingComponent
from horizons.component.componentholder import ComponentHolder
from horizons.component.storagecomponent import StorageComponent
from horizons.constants import GAME, LAYERS, RES
from horizons.i18n import disable_translations
from horizons.scheduler import Scheduler
from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.util.shapes import ConstRect, Point, distances
from horizons.util.worldobject import WorldObject
from horizons.world.building.buildable import BuildableSingle
from horizons.world.concreteobject import ConcreteObject
from horizons.world.settlement import Settlement


class BasicBuilding(ComponentHolder, ConcreteObject):
	"""Class that represents a building. The building class is mainly a super class for other buildings."""

	# basic properties of class
	walkable = False # whether we can walk on this building (True for e.g. streets, trees..)
	buildable_upon = False # whether we can build upon this building
	is_building = True
	tearable = True
	layer = LAYERS.OBJECTS

	log = logging.getLogger("world.building")

	"""
	@param x, y: int position of the building.
	@param rotation: value passed to getInstance
	@param owner: Player that owns the building.
	@param level: start in this tier
	@param action_set_id: use this action set id. None means choose one at random
	"""
	def __init__(self, x, y, rotation, owner, island, level=None, **kwargs):
		self.__pre_init(owner, rotation, Point(x, y), level=level)
		super().__init__(x=x, y=y, rotation=rotation, owner=owner,
		                                    island=island, **kwargs)
		self.__init()
		self.island = island

		settlements = self.island.get_settlements(self.position, owner)
		self.settlement = None
		if settlements:
			self.settlement = settlements[0]
		elif owner:
			# create one if we have an owner
			self.settlement = self.island.add_settlement(self.position, self.radius, owner)

		assert self.settlement is None or isinstance(self.settlement, Settlement)

	def __pre_init(self, owner, rotation, origin, level=None):
		"""Here we face the awkward situation of requiring a fourth init function.
		It is called like __init, but before other parts are inited via super().
		This is necessary since some attributes are used by these other parts."""
		self.owner = owner
		if level is None:
			level = 0 if self.owner is None else self.owner.settler_level
		self.level = level
		self.rotation = rotation
		if self.rotation in (135, 315): # Rotate the rect correctly
			self.position = ConstRect(origin, self.size[1] - 1, self.size[0] - 1)
		else:
			self.position = ConstRect(origin, self.size[0] - 1, self.size[1] - 1)

	def __init(self, remaining_ticks_of_month=None):
		self.loading_area = self.position # shape where collector get resources

		origin = self.position.origin
		self._instance, action_name = self.getInstance(self.session, origin.x, origin.y,
		    rotation=self.rotation, action_set_id=self._action_set_id, world_id=str(self.worldid))

		if self.has_running_costs: # Get payout every 30 seconds
			interval = self.session.timer.get_ticks(GAME.INGAME_TICK_INTERVAL)
			run_in = remaining_ticks_of_month if remaining_ticks_of_month is not None else interval
			Scheduler().add_new_object(self.get_payout, self,
			                           run_in=run_in, loops=-1, loop_interval=interval)

	def toggle_costs(self):
		self.running_costs, self.running_costs_inactive = \
				self.running_costs_inactive, self.running_costs

	def running_costs_active(self):
		"""Returns whether the building currently pays the running costs for status 'active'"""
		return (self.running_costs > self.running_costs_inactive)

	def get_payout(self):
		"""Gets the payout from the settlement in form of its running costs"""
		self.owner.get_component(StorageComponent).inventory.alter(RES.GOLD, -self.running_costs)

	def remove(self):
		"""Removes the building"""
		self.log.debug("building: remove %s", self.worldid)
		if hasattr(self, "disaster"):
			self.disaster.recover(self)
		self.island.remove_building(self)
		super().remove()
		# NOTE: removing layers from the renderer here will affect others players too!

	def save(self, db):
		super().save(db)
		db("INSERT INTO building (rowid, type, x, y, rotation, location, level) \
		   VALUES (?, ?, ?, ?, ?, ?, ?)",
		                                self.worldid, self.__class__.id, self.position.origin.x,
		                                self.position.origin.y, self.rotation,
		                                (self.settlement or self.island).worldid, self.level)
		if self.has_running_costs:
			remaining_ticks = Scheduler().get_remaining_ticks(self, self.get_payout)
			db("INSERT INTO remaining_ticks_of_month(rowid, ticks) VALUES(?, ?)", self.worldid, remaining_ticks)

	def load(self, db, worldid):
		self.island, self.settlement = self.load_location(db, worldid)
		x, y, location, rotation, level = db.get_building_row(worldid)
		owner_id = db.get_settlement_owner(location)
		owner = None if owner_id is None else WorldObject.get_object_by_id(owner_id)

		# early init before super() call
		self.__pre_init(owner, rotation, Point(x, y), level=level)

		super().load(db, worldid)

		remaining_ticks_of_month = None
		if self.has_running_costs:
			db_data = db("SELECT ticks FROM remaining_ticks_of_month WHERE rowid=?", worldid)
			if not db_data:
				# this can happen when running costs are set when there were no before
				# we shouldn't crash because of changes in yaml code, still it's suspicious
				self.log.warning('Object %s of type %s does not know when to pay its rent.\n'
					'Disregard this when loading old savegames or on running cost changes.',
					self.worldid, self.id)
				remaining_ticks_of_month = 1
			else:
				remaining_ticks_of_month = db_data[0][0]

		self.__init(remaining_ticks_of_month=remaining_ticks_of_month)

		# island.add_building handles registration of building for island and settlement
		self.island.add_building(self, self.owner, load=True)

	def load_location(self, db, worldid):
		"""
		Does not alter self, just gets island and settlement from a savegame.
		@return: tuple: (island, settlement)
		"""
		location_obj = WorldObject.get_object_by_id(db.get_building_location(worldid))
		if isinstance(location_obj, Settlement):
			# workaround: island can't be fetched from world, because it isn't fully constructed
			island = WorldObject.get_object_by_id(db.get_settlement_island(location_obj.worldid))
			settlement = location_obj
		else: # loc is island
			island = location_obj
			settlement = None
		return (island, settlement)

	def get_buildings_in_range(self):
		# TODO Think about moving this to the Settlement class
		buildings = self.settlement.buildings
		for building in buildings:
			if building is self:
				continue
			if distances.distance_rect_rect(self.position, building.position) <= self.radius:
				yield building

	def update_action_set_level(self, level=0):
		"""Updates this buildings action_set to a random actionset from the specified level
		(if an action set exists in that level).
		Its difference to get_random_action_set is that it just checks one level, and doesn't
		search for an action set everywhere, which makes it a lot more effective if you're
		just updating.
		@param level: int level number"""
		action_set = self.__class__.get_random_action_set(level, exact_level=True)
		if action_set:
			self._action_set_id = action_set  # Set the new action_set
			self.act(self._action, repeating=True)

	def level_upgrade(self, lvl):
		"""Upgrades building to another tier"""
		self.level = lvl
		self.update_action_set_level(lvl)

		# any collectors (units) should also be upgraded, so that their
		# graphics or properties can change
		if self.has_component(CollectingComponent):
			for collector in self.get_component(CollectingComponent).get_local_collectors():
				collector.level_upgrade(lvl)

	@classmethod
	def get_initial_level(cls, player):
		if hasattr(cls, 'default_level_on_build'):
			return cls.default_level_on_build
		return player.settler_level

	@classmethod
	def getInstance(cls, session, x, y, action='idle', level=0, rotation=45, action_set_id=None, world_id=""):
		"""Get a Fife instance
		@param x, y: The coordinates
		@param action: The action, defaults to 'idle'
		@param level: object level. Relevant for choosing an action set
		@param rotation: rotation of the object. Any of [ 45 + 90*i for i in xrange(0, 4) ]
		@param action_set_id: can be set if the action set is already known. If set, level isn't considered.
		@return: tuple (fife_instance, action_set_id)
		"""
		assert isinstance(x, int)
		assert isinstance(y, int)
		#rotation = cls.check_build_rotation(session, rotation, x, y)
		# TODO: replace this with new buildable api
		# IDEA: save rotation in savegame

		width, length = cls.size
		if rotation == 135 or rotation == 315:
			# if you look at a non-square builing from a 45 degree angle it looks
			# different than from a 135 degree angle
			# when you rotate it the width becomes the length and the length becomes the width
			width, length = length, width

		# the drawing origin is the center of it's area, minus 0.5
		# the 0.5 isn't really necessary, but other code is aligned with the 0.5 shift
		# this is at least for the gridoverlay, and the location of a build preview relative to the mouse
		# it this is changed, it should also be changed for ground tiles (world/ground.py) and units
		instance_coords = [x + width / 2 - 0.5, y + length / 2 - 0.5, 0]

		instance = session.view.layers[cls.layer].createInstance(
			cls._fife_object,
			fife.ExactModelCoordinate(*instance_coords),
			world_id)

		if action_set_id is None:
			action_set_id = cls.get_random_action_set(level=level)
		fife.InstanceVisual.create(instance)

		action_set = ActionSetLoader.get_set(action_set_id)
		if action not in action_set:
			if 'idle' in action_set:
				action = 'idle'
			elif 'idle_full' in action_set:
				action = 'idle_full'
			else:
				# set first action
				action = list(action_set.keys())[0]
		instance.actRepeat("{}_{}".format(action, action_set_id), rotation)
		return (instance, action_set_id)

	@classmethod
	def have_resources(cls, inventory_holders, owner):
		return Build.check_resources({}, cls.costs, owner, inventory_holders)[0]

	def init(self):
		"""init the building, called after the constructor is run and the
		building is positioned (the settlement variable is assigned etc)
		"""
		pass

	def start(self):
		"""This function is called when the building is built,
		to start production for example."""
		pass

	def __str__(self):
		with disable_translations():
			return '{}(id={};worldid={})'.format(self.name, self.id, getattr(self, 'worldid', 'none'))


class DefaultBuilding(BasicBuilding, BuildableSingle):
	"""Building with default properties, that does nothing."""
	pass
