# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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
import logging
import random

import fife

import horizons.main

from horizons.world.settlement import Settlement
from horizons.world.ambientsound import AmbientSound
from horizons.util import Rect, Point, WorldObject
from horizons.constants import RES, LAYERS


class BasicBuilding(AmbientSound, WorldObject):
	"""Class that represents a building. The building class is mainly a super class for other buildings.
	@param x, y: int position of the building.
	@param owner: Player that owns the building.
	@param instance: fife.Instance - only singleplayer: preview instance from the buildingtool."""
	part_of_nature = False # wether this is part of nature (free units can walk through it)
	walkable = False # wether we can walk on this building (true for e.g. streets, trees..)
	object_type = 0

	log = logging.getLogger("world.building")

	def __init__(self, x, y, rotation, owner, island, instance = None, **kwargs):
		super(BasicBuilding, self).__init__(x=x, y=y, rotation=rotation, owner=owner, \
																				instance=instance, island=island, **kwargs)
		self.__init(Point(x, y), rotation, owner, instance)
		self.island = weakref.ref(island)
		self.settlement = self.island().get_settlement(Point(x, y)) or \
			self.island().add_settlement(self.position, self.radius, owner) if \
			owner is not None else None

	def __init(self, origin, rotation, owner, instance):
		self._action_set_id = horizons.main.db("SELECT action_set_id FROM data.action_set WHERE object_id=? ORDER BY random() LIMIT 1", self.id)[0][0]
		self.position = Rect(origin, self.size[0]-1, self.size[1]-1)
		self.rotation = rotation
		self.owner = owner
		self._instance = self.getInstance(origin.x, origin.y, rotation = rotation) if instance is None else instance
		self._instance.setId(str(self.getId()))

		if self.running_costs != 0: # Get payout every 30 seconds
			horizons.main.session.scheduler.add_new_object(self.get_payout, self, runin=horizons.main.session.timer.get_ticks(30), loops=-1)

		# play ambient sound, if available
		for soundfile in self.soundfiles:
			self.play_ambient(soundfile, True)

	def toggle_costs(self):
		self.running_costs , self.running_costs_inactive = \
			self.running_costs_inactive, self.running_costs

	def get_payout(self):
		"""gets the payout from the settlement in form of it's running costs"""
		self.settlement.owner.inventory.alter(RES.GOLD_ID, -self.running_costs)

	def act(self, action, facing_loc=None, repeating=False):
		if facing_loc is None:
			facing_loc = self._instance.getFacingLocation()
		if not action in horizons.main.action_sets[self._action_set_id]:
			action = 'idle'
		self._instance.act(action+"_"+str(self._action_set_id), facing_loc, repeating)

	def remove(self):
		"""Removes the building"""
		self.log.debug("BUILDING: REMOVE %s", self.getId())
		self.island().remove_building(self)
		self._instance.getLocationRef().getLayer().deleteInstance(self._instance)
		self._instance = None
		horizons.main.session.scheduler.rem_all_classinst_calls(self)
		#instance is owned by layer...
		#self._instance.thisown = 1
		self.__del__()

	def __del__(self):
		super(BasicBuilding, self).__del__()

	def save(self, db):
		super(BasicBuilding, self).save(db)
		db("INSERT INTO building (rowid, type, x, y, rotation, health, location) \
		   VALUES (?, ?, ?, ?, ?, ?, ?)", \
			self.getId(), self.__class__.id, self.position.origin.x, \
			self.position.origin.y, self.rotation, \
			self.health, (self.settlement or self.island()).getId())

	def load(self, db, worldid):
		self.log.debug('loading building %s', worldid)
		super(BasicBuilding, self).load(db, worldid)
		x, y, self.health, location, rotation = \
			db("SELECT x, y, health, location, rotation FROM building WHERE rowid = ?", worldid)[0]

		owner_db = db("SELECT owner FROM settlement WHERE rowid = ?", location)
		owner = None if len(owner_db) == 0 else WorldObject.get_object_by_id(owner_db[0][0])

		self.__init(Point(x, y), rotation, owner, None)

		island, self.settlement = self.load_location(db, worldid)
		self.island = weakref.ref(island)

		self.island().add_building(self, self.owner)

	def load_location(self, db, worldid):
		"""
		Does not alter self, just gets island and settlement from a savegame.
		@return: tuple: (island, settlement)
		"""
		location = db("SELECT location FROM building WHERE rowid = ?", worldid)[0][0]
		location_obj = WorldObject.get_object_by_id(location)
		if isinstance(location_obj, Settlement):
			# workaround: island can't be fetched from world, because it isn't fully constructed
			island_id = db("SELECT island FROM settlement WHERE rowid = ?", location_obj.getId())[0][0]
			island = WorldObject.get_object_by_id(island_id)
			settlement = island.get_settlement(self.position.center()) or \
					island.add_existing_settlement(self.position, self.radius, location_obj)
		else: # loc is island
			island = location_obj
			settlement = None
		return (island, settlement)

	def is_part_of_nature(self):
		return self.part_of_nature

	def is_walkable(self):
		return self.walkable

	def get_buildings_in_range(self):
		# TODO Think about moving this to the Settlement class
		buildings = self.settlement.buildings
		ret_building = []
		for building in buildings:
			if building == self:
				continue
			if self.position.distance( building.position ) <= self.radius:
				ret_building.append( building )
		return ret_building

	@classmethod
	def getInstance(cls, x, y, action='idle', building=None, layer=LAYERS.OBJECTS, rotation=0, **trash):
		"""Get a Fife instance
		@param x, y: The coordinates
		@param action: The action, defaults to 'idle'
		@param building: This parameter is used for overriding the class that handles the building, setting this to another building class makes the function redirect the call to that class
		@param **trash: sometimes we get more keys we are not interested in
		"""
		if building is not None:
			return building.getInstance(x = x, y = y, action=action, layer=layer, rotation=rotation, **trash)
		else:
			facing_loc = fife.Location(horizons.main.session.view.layers[layer])
			if rotation == 45:
				instance = horizons.main.session.view.layers[layer].createInstance(cls._object, fife.ModelCoordinate(int(x), int(y), 0))
				facing_loc.setLayerCoordinates(fife.ModelCoordinate(int(x+cls.size[0]+3), int(y), 0))
			elif rotation == 135:
				instance = horizons.main.session.view.layers[layer].createInstance(cls._object, fife.ModelCoordinate(int(x), int(y + cls.size[1] - 1), 0))
				facing_loc.setLayerCoordinates(fife.ModelCoordinate(int(x), int(y-cls.size[1]-3), 0))
			elif rotation == 225:
				instance = horizons.main.session.view.layers[layer].createInstance(cls._object, fife.ModelCoordinate(int(x + cls.size[0] - 1), int(y + cls.size[1] - 1), 0))
				facing_loc.setLayerCoordinates(fife.ModelCoordinate(int(x-cls.size[0]-3), int(y), 0))
			elif rotation == 315:
				instance = horizons.main.session.view.layers[layer].createInstance(cls._object, fife.ModelCoordinate(int(x + cls.size[0] - 1), int(y), 0))
				facing_loc.setLayerCoordinates(fife.ModelCoordinate(int(x), int(y+cls.size[1]+3), 0))
			else:
				return None
			action_set_id  = horizons.main.db("SELECT action_set_id FROM data.action_set WHERE object_id=? order by random() LIMIT 1", cls.id)[0][0]
			fife.InstanceVisual.create(instance)
			if action in horizons.main.action_sets[action_set_id]:
				pass
			elif 'idle' in horizons.main.action_sets[action_set_id]:
				action='idle'
			elif 'idle_full' in horizons.main.action_sets[action_set_id]:
				action='idle_full'
			else:
				# set first action
				action=horizons.main.action_sets[action_set_id].keys()[0]

			instance.act(action+"_"+str(action_set_id), facing_loc, True)
			return instance

	@classmethod
	def get_build_costs(self, building=None, **trash):
		"""Get the costs for the building
		@param **trash: we normally dont need any parameter, but we get the same as the getInstance function
		"""
		if building is not None:
			return building.get_build_costs(**trash)
		else:
			return self.costs

	def init(self):
		"""init the building, called after the constructor is run and the building is positioned (the settlement variable is assigned etc)
		"""
		pass

	def start(self):
		"""This function is called when the building is built, to start production for example."""
		pass

	def production_state_changed(self):
		"""Called when the building's production did something (i.e. start, stop, etc.)."""
		# TODO React to state changes
		#if "work" in horizons.main.action_sets[self._action_set_id]:
		#	self.act("work", self._instance.getFacingLocation(), True)
		#else:
		#	self.act("idle", self._instance.getFacingLocation(), True)
		# TODO: implement animation change when we have production states as well as toggle_costs
		pass

	def __str__(self): # debug
		classname = horizons.main.db("SELECT name FROM building where id = ?", self.id)[0][0]
		# must not call getId if obj has no id, cause it changes the program
		worldid = None if not hasattr(self, '_WorldObject__id') else self.getId()
		return classname+'(id=%s;worldid=%s)' % (self.id, worldid)



class Selectable(object):
	def select(self):
		"""Runs neccesary steps to select the building."""
		renderer = horizons.main.session.view.renderer['InstanceRenderer']
		renderer.addOutlined(self._instance, 255, 255, 255, 1)
		for tile in self.island().grounds:
			if tile.settlement == self.settlement and \
				 self.position.distance(Point(tile.x, tile.y)) <= self.radius and \
				 any(x in tile.__class__.classes for x in ('constructible', 'coastline')):
				renderer.addColored(tile._instance, 255, 255, 255)
				if tile.object is not None:
					renderer.addColored(tile.object._instance, 255, 255, 255)

	def deselect(self):
		"""Runs neccasary steps to deselect the unit."""
		renderer = horizons.main.session.view.renderer['InstanceRenderer']
		renderer.removeOutlined(self._instance)
		renderer.removeAllColored()
