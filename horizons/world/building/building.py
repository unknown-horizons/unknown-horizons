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

import logging

import fife

import horizons.main
from horizons.scheduler import Scheduler

from horizons.world.concreteobject import ConcretObject
from horizons.world.settlement import Settlement
from horizons.world.ambientsound import AmbientSound
from horizons.util import Rect, Point, WorldObject, ActionSetLoader, decorators
from horizons.constants import RES, LAYERS, GAME
from horizons.world.building.buildable import BuildableSingle


class BasicBuilding(AmbientSound, ConcretObject):
	"""Class that represents a building. The building class is mainly a super class for other buildings.
	@param x, y: int position of the building.
	@param owner: Player that owns the building.
	@param instance: fife.Instance - only singleplayer: preview instance from the buildingtool."""
	walkable = False # whether we can walk on this building (true for e.g. streets, trees..)
	buildable_upon = False # whether we can build upon this building
	is_building = True

	log = logging.getLogger("world.building")

	def __init__(self, x, y, rotation, owner, island, instance = None, **kwargs):
		super(BasicBuilding, self).__init__(x=x, y=y, rotation=rotation, owner=owner, \
																				instance=instance, island=island, **kwargs)
		self.__init(Point(x, y), rotation, owner, instance)
		self.island = island
		self.settlement = self.island.get_settlement(Point(x, y)) or \
			self.island.add_settlement(self.position, self.radius, owner) if \
			owner is not None else None

	def __init(self, origin, rotation, owner, instance):
		self._action_set_id = horizons.main.db("SELECT action_set_id FROM data.action_set WHERE object_id=? ORDER BY random() LIMIT 1", self.id)[0][0]
		self.position = Rect(origin, self.size[0]-1, self.size[1]-1)
		self.rotation = rotation
		self.owner = owner
		self._instance = self.getInstance(self.session, origin.x, origin.y, rotation = rotation) if \
		    instance is None else instance
		self._instance.setId(str(self.getId()))

		if self.running_costs != 0: # Get payout every 30 seconds
			Scheduler().add_new_object(self.get_payout, self, \
			     runin=self.session.timer.get_ticks(GAME.INGAME_TICK_INTERVAL), loops=-1)

		# play ambient sound, if available
		for soundfile in self.soundfiles:
			self.play_ambient(soundfile, True)

	def toggle_costs(self):
		self.running_costs , self.running_costs_inactive = \
			self.running_costs_inactive, self.running_costs

	def running_costs_active(self):
		return (self.running_costs > self.running_costs_inactive)

	def get_payout(self):
		"""gets the payout from the settlement in form of it's running costs"""
		self.owner.inventory.alter(RES.GOLD_ID, -self.running_costs)

	def remove(self):
		"""Removes the building"""
		self.log.debug("building: remove %s", self.getId())
		self.island.remove_building(self)
		#instance is owned by layer...
		#self._instance.thisown = 1
		super(BasicBuilding, self).remove()
		renderer = self.session.view.renderer['InstanceRenderer']
		renderer.removeOutlined(self._instance)
		renderer.removeAllColored()

	def save(self, db):
		super(BasicBuilding, self).save(db)
		db("INSERT INTO building (rowid, type, x, y, rotation, health, location) \
		   VALUES (?, ?, ?, ?, ?, ?, ?)", \
			self.getId(), self.__class__.id, self.position.origin.x, \
			self.position.origin.y, self.rotation, \
			self.health, (self.settlement or self.island).getId())

	def load(self, db, worldid):
		super(BasicBuilding, self).load(db, worldid)
		x, y, self.health, location, rotation = \
			db("SELECT x, y, health, location, rotation FROM building WHERE rowid = ?", worldid)[0]

		owner_db = db("SELECT owner FROM settlement WHERE rowid = ?", location)
		owner = None if len(owner_db) == 0 else WorldObject.get_object_by_id(owner_db[0][0])

		self.__init(Point(x, y), rotation, owner, None)

		self.island, self.settlement = self.load_location(db, worldid)

		# island.add_building handles registration of building for island and settlement
		self.island.add_building(self, self.owner)

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
			# settlement might not have been registered in island, so do it if getter fails
			settlement = island.get_settlement(self.position.center()) or \
					island.add_existing_settlement(self.position, self.radius, location_obj)
		else: # loc is island
			island = location_obj
			settlement = None
		return (island, settlement)

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
	def getInstance(cls, session, x, y, action='idle', building=None, layer=LAYERS.OBJECTS, rotation=0, **trash):
		"""Get a Fife instance
		@param x, y: The coordinates
		@param action: The action, defaults to 'idle'
		@param building: This parameter is used for overriding the class that handles the building, setting this to another building class makes the function redirect the call to that class
		@param **trash: sometimes we get more keys we are not interested in
		"""
		assert isinstance(x, int)
		assert isinstance(y, int)
		if building is not None:
			return building.getInstance(session = session, x = x, y = y, action=action, layer=layer, \
			                            rotation=rotation, **trash)
		else:
			rotation = cls.check_build_rotation(rotation, x, y)
			facing_loc = fife.Location(session.view.layers[layer])
			instance_coords = list((x, y, 0))
			layer_coords = list((x, y, 0))
			if rotation == 45:
				layer_coords[0] = x+cls.size[0]+3
			elif rotation == 135:
				instance_coords[1] = y + cls.size[1] - 1
				layer_coords[1] = y-cls.size[1]-3
			elif rotation == 225:
				instance_coords = list(( x + cls.size[0] - 1, y + cls.size[1] - 1, 0))
				layer_coords[0] = x-cls.size[0]-3
			elif rotation == 315:
				instance_coords[0] = x + cls.size[0] - 1
				layer_coords[1] = y+cls.size[1]+3
			else:
				return None
			instance = session.view.layers[layer].createInstance(cls._object, \
			                         fife.ModelCoordinate(*instance_coords))
			facing_loc.setLayerCoordinates(fife.ModelCoordinate(*layer_coords))

			action_set_id  = horizons.main.db("SELECT action_set_id FROM data.action_set WHERE object_id=? order by random() LIMIT 1", cls.id)[0][0]
			fife.InstanceVisual.create(instance)

			action_sets = ActionSetLoader.get_action_sets()
			if not action in action_sets[action_set_id]:
				if 'idle' in action_sets[action_set_id]:
					action='idle'
				elif 'idle_full' in action_sets[action_set_id]:
					action='idle_full'
				else:
					# set first action
					action = action_sets[action_set_id].keys()[0]

			instance.act(action+"_"+str(action_set_id), facing_loc, True)
			return instance

	@classmethod
	def check_build_rotation(cls, rotation, x, y):
		"""Returns a possible rotation for this building.
		Overwrite to specify rotation restrictions (e.g. water-side buildings)
		@param rotation: The prefered rotation
		@param x, y: int coords
		@return: integer, rotation in degrees"""
		return rotation

	@classmethod
	def get_build_costs(self, building=None, **trash):
		"""Get the costs for the building
		@param **trash: we normally don't need any parameter, but we get the same as the getInstance function
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

	def __str__(self): # debug
		classname = horizons.main.db("SELECT name FROM building where id = ?", self.id)[0][0]
		return '%s(id=%s;worldid=%s)' % (classname, self.id, \
																		 self.getId(create_if_nonexistent=False))



class SelectableBuilding(object):
	range_applies_only_on_island = True
	selection_color = (255, 0, 255)

	def select(self):
		"""Runs necessary steps to select the building."""
		renderer = self.session.view.renderer['InstanceRenderer']
		renderer.addOutlined(self._instance, self.selection_color[0], self.selection_color[1], \
		                     self.selection_color[2], 1)
		self._do_select(renderer, self.position, self.session.world, self.settlement)

	def deselect(self):
		"""Runs neccassary steps to deselect the building."""
		renderer = self.session.view.renderer['InstanceRenderer']
		renderer.removeOutlined(self._instance)
		renderer.removeAllColored()

	def remove(self):
		super(SelectableBuilding, self).remove()
		self.deselect()

	@classmethod
	def select_building(cls, session, position, settlement):
		"""Select a hypothecial instance of this class. Use Case: Buildingtool.
		Only works on a subclass of BuildingClass, since it requires certain class attributes.
		@param session: Session instance
		@param position: Position of building, usually Rect
		@param settlement: Settlement instance the building belongs to"""
		renderer = session.view.renderer['InstanceRenderer']
		cls._do_select(renderer, position, session.world, settlement)

	@classmethod
	def deselect_building(cls, session):
		session.view.renderer['InstanceRenderer'].removeAllColored()

	@classmethod
	@decorators.make_constants()
	def _do_select(cls, renderer, position, world, settlement):
		add_colored = renderer.addColored
		if cls.range_applies_only_on_island:
			island = world.get_island(position.origin)
			if island is None:
				return # preview isn't on island, and therefore invalid
			for coord in position.get_radius_coordinates(cls.radius, include_self=True):
				tile = island.get_tile_tuple(coord)
				try:
					if tile.settlement == settlement and \
					   ( 'constructible' in tile.classes or 'coastline' in tile.classes ):
						add_colored(tile._instance, *cls.selection_color)
						add_colored(tile.object._instance, *cls.selection_color)
				except AttributeError:
					pass # no tile or object on tile
		else:
			# we have to color water too
			for tile in world.get_tiles_in_radius(position.center(), cls.radius):
				if hasattr(tile, 'settlement') and tile.settlement != self.settlement:
					continue # don't color enemy grounds
				add_colored(tile._instance, *self.selection_color)
				if hasattr(tile, 'object') and tile.object is not None:
					add_colored(tile.object._instance, *self.selection_color)


class DefaultBuilding(BasicBuilding, SelectableBuilding, BuildableSingle):
	"""Building with default properties, that does nothing."""
	pass
