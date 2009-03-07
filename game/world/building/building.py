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

import math
import weakref

import fife

import game.main
from game.world.settlement import Settlement
from game.world.ambientsound import AmbientSound
from game.util import Rect,Point, WorldObject

class Building(AmbientSound, WorldObject):
	"""Class that represents a building. The building class is mainly a super class for other buildings.
	@param x, y: int position of the building.
	@param owner: Player that owns the building.
	@param instance: fife.Instance - only singleplayer: preview instance from the buildingtool."""
	def __init__(self, x, y, rotation, owner, instance = None, **kwargs):
		super(Building, self).__init__(x=x, y=y, rotation=rotation, owner=owner, instance=instance, **kwargs)
		if game.main.debug:
			print "Initing Building", self.id
		self.__init(Point(x,y), rotation, owner, instance)
		self.island = weakref.ref(game.main.session.world.get_island(x, y))
		self.settlement = self.island().get_settlement(Point(x,y)) or \
			self.island().add_settlement(self.position, self.radius, owner) if \
			owner is not None else None

	def __init(self, origin, rotation, owner, instance):
		self._action_set_id = game.main.db("SELECT action_set_id FROM data.action_set WHERE building_id=? order by random() LIMIT 1", self.id)[0][0]
		self.position = Rect(origin, self.size[0]-1, self.size[1]-1)
		self.rotation = rotation
		self.owner = owner
		self.object_type = 0
		self._instance = self.getInstance(origin.x, origin.y, rotation = rotation) if instance is None else instance
		self._instance.setId(str(self.getId()))

		if self.running_costs != 0:
			game.main.session.scheduler.add_new_object(self.get_payout, self, runin=game.main.session.timer.get_ticks(30), loops=-1)

		# play ambient sound, if available
		for (soundfile,) in game.main.db("SELECT file FROM sounds INNER JOIN building_sounds ON \
		sounds.rowid = building_sounds.sound AND building_sounds.building = ?", self.id):
			self.play_ambient(soundfile, True)

	def toggle_costs(self):
			self.running_costs , self.running_costs_inactive = \
					self.running_costs_inactive, self.running_costs

	def get_payout(self):
		"""gets the payout from the settlement in form of it's running costs"""
		self.settlement.owner.inventory.alter(1, -self.running_costs)

	def act(self, action, facing_loc, repeating=False):
		self._instance.act(action+"_"+str(self._action_set_id),facing_loc,repeating)

	def remove(self):
		"""Removes the building"""
		if game.main.debug:
			print "BUILDING: REMOVE %s" % self.getId()
		if self.settlement is not None:
			self.settlement.rem_inhabitants(self.inhabitants)
		self.island().remove_building(self)
		game.main.session.ingame_gui.hide_menu()

		for x in xrange(self.position.left, self.position.right + 1):
			for y in xrange(self.position.top, self.position.bottom + 1):
				point = Point(x, y)
				tile = self.island().get_tile(point)
				tile.blocked = False
				tile.object = None
		self._instance.getLocationRef().getLayer().deleteInstance(self._instance)
		#instance is owned by layer...
		#self._instance.thisown = 1
		self.__del__()

	def __del__(self):
		super(Building, self).__del__()

	def save(self, db):
		super(Building, self).save(db)
		db("INSERT INTO building (rowid, type, x, y, rotation, health, location) \
		   VALUES (?, ?, ?, ?, ?, ?, ?)", \
			self.getId(), self.__class__.id, self.position.origin.x, \
			self.position.origin.y, self.rotation, \
			self.health, (self.settlement or self.island()).getId())

	def load(self, db, worldid):
		if game.main.debug:
			print 'loading building', worldid
		super(Building, self).load(db, worldid)
		x, y, health, location, rotation = \
			db("SELECT x, y, health, location, rotation FROM building WHERE rowid = ?", worldid)[0]

		owner_db = db("SELECT owner FROM settlement WHERE rowid = ?", location)
		owner = None if len(owner_db) == 0 else WorldObject.getObjectById(owner_db[0][0])

		self.__init(Point(x,y), rotation, owner, None)

		location_obj = WorldObject.getObjectById(location)
		if isinstance(location_obj, Settlement):
			# workaround: island can't be fetched from world, because it
			# isn't fully constructed, when this code is executed
			island_id = db("SELECT island FROM settlement WHERE rowid = ?", location_obj.getId())[0][0]
			self.island = weakref.ref(WorldObject.getObjectById(island_id))
			self.settlement = self.island().get_settlement(Point(x,y)) or \
					self.island().add_existing_settlement(self.position, self.radius, location_obj)
		else: # loc is island
			from game.world.island import Island
			assert(isinstance(location_obj, Island))

			self.island = weakref.ref(location_obj)
			self.settlement = None

		self.island().add_building(self, self.owner)

	def get_buildings_in_range(self):
		buildings = self.settlement.buildings
		ret_building = []
		for building in buildings:
			if building == self:
				continue
			if self.position.distance( building.position ) <= self.radius:
				ret_building.append( building )
		return ret_building

	@classmethod
	def getInstance(cls, x, y, action='idle', building=None, layer=2, rotation=0, **trash):
		"""Get a Fife instance
		@param x, y: The coordinates
		@param action: The action, defaults to 'idle'
		@param building: This parameter is used for overriding the class that handles the building, setting this to another building class makes the function redirect the call to that class
		@param **trash: sometimes we get more keys we are not interested in
		"""
		if building is not None:
			return building.getInstance(x = x, y = y, action=action, layer=layer,rotation=rotation, **trash)
		else:
			facing_loc = fife.Location(game.main.session.view.layers[layer])
			if rotation == 45:
				instance = game.main.session.view.layers[layer].createInstance(cls._object, fife.ModelCoordinate(int(x), int(y), 0))
				facing_loc.setLayerCoordinates(fife.ModelCoordinate(int(x+cls.size[0]+3), int(y), 0))
			elif rotation == 135:
				instance = game.main.session.view.layers[layer].createInstance(cls._object, fife.ModelCoordinate(int(x), int(y + cls.size[1] - 1), 0))
				facing_loc.setLayerCoordinates(fife.ModelCoordinate(int(x), int(y-cls.size[1]-3), 0))
			elif rotation == 225:
				instance = game.main.session.view.layers[layer].createInstance(cls._object, fife.ModelCoordinate(int(x + cls.size[0] - 1), int(y + cls.size[1] - 1), 0))
				facing_loc.setLayerCoordinates(fife.ModelCoordinate(int(x-cls.size[0]-3), int(y), 0))
			elif rotation == 315:
				instance = game.main.session.view.layers[layer].createInstance(cls._object, fife.ModelCoordinate(int(x + cls.size[0] - 1), int(y), 0))
				facing_loc.setLayerCoordinates(fife.ModelCoordinate(int(x), int(y+cls.size[1]+3), 0))
			else:
				return None
			action_set_id  = game.main.db("SELECT action_set_id FROM data.action_set WHERE building_id=? order by random() LIMIT 1", cls.id)[0][0]
			fife.InstanceVisual.create(instance)
			if action in game.main.action_sets[action_set_id].keys():
				pass
			elif 'idle' in game.main.action_sets[action_set_id].keys():
				action='idle'
			elif 'idle_full' in game.main.action_sets[action_set_id].keys():
				action='idle_full'
			else:
				action=game.main.action_sets[action_set_id].keys()[0]

			instance.act(action+"_"+str(action_set_id), facing_loc, True)
			return instance

	@classmethod
	def getBuildCosts(self, building=None, **trash):
		"""Get the costs for the building
		@param **trash: we normally dont need any parameter, but we get the same as the getInstance function
		"""
		if building is not None:
			return building.getBuildCosts(**trash)
		else:
			return self.costs

	def init(self):
		"""init the building, called after the constructor is run and the building is positioned (the settlement variable is assigned etc)
		"""
		if self.settlement:
			self.settlement.add_inhabitants(self.inhabitants)

	def start(self):
		"""This function is called when the building is built, to start production for example."""
		pass

class Selectable(object):
	def select(self):
		"""Runs neccesary steps to select the building."""
		game.main.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, 1)
		for tile in self.island().grounds:
			if tile.settlement == self.settlement and (max(self.position.left - tile.x, 0, tile.x - self.position.right) ** 2) + (max(self.position.top - tile.y, 0, tile.y - self.position.bottom) ** 2) <= self.radius ** 2 and any(x in tile.__class__.classes for x in ('constructible', 'coastline')):
				game.main.session.view.renderer['InstanceRenderer'].addColored(tile._instance, 255, 255, 255)
				if tile.object is not None and True: #todo: only highlight buildings that produce something were interested in
					game.main.session.view.renderer['InstanceRenderer'].addColored(tile.object._instance, 255, 255, 255)

	def deselect(self):
		"""Runs neccasary steps to deselect the unit."""
		game.main.session.view.renderer['InstanceRenderer'].removeOutlined(self._instance)
		game.main.session.view.renderer['InstanceRenderer'].removeAllColored()
