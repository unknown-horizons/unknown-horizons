# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

import game.main

import math
import fife
from game.gui.selectiontool import SelectionTool
from game.world.building import building
from game.world.units.ship import Ship
from game.world.player import Player
from game.gui.ingamegui import IngameGui
from game.gui.ingamekeylistener import IngameKeyListener
from game.world.island import Island
from game.timer import Timer
from game.scheduler import Scheduler
from game.manager import SPManager
from game.view import View
from game.world import World
from game.entities import Entities

class Game(object):
	"""Game class represents the games main ingame view and controls cameras and map loading."""
	def init(self):
		#game
		self.timer = Timer(16)
		self.manager = SPManager()
		self.scheduler = Scheduler()
		self.view = View()
		self.entities = Entities()

		#GUI
		self.ingame_gui = IngameGui()
		self.keylistener = IngameKeyListener()
		self.cursor = SelectionTool()

		#to be (re)moved:
		self.uid = 0
		self.selected_instance = None
		self.instance_to_unit = {}

	def loadmap(self, map):
		"""Loads a map.
		@var map: string with the mapfile path.
		"""

		#load map
		game.main.db.query("attach ? as map", (map))
		self.world = World()

		#temporary ship creation, should be done automatically in later releases
		#inst = self.create_instance(self.view.layers[1], 'building', '99', 25, 25)
		#ship = self.create_unit(self.view.layers[1], str(self.uid-1), 99, Ship)

		#setup view
		self.view.center(((self.world.max_x - self.world.min_x) / 2.0), ((self.world.max_y - self.world.min_y) / 2.0))

		print self.view.model.getNamespaces()

	def create_unit(self, layer, id, object_id, UnitClass):
		"""
		DEPRECATED: To build a building use the Build CommandClass. Create_unit is only used for the temporary ship!
		
		Creates a new unit an the specified layer
		@var layer: fife.Layer the unit is to be created on
		@var id: str containing the object's id
		@var object_id: int containing the objects id in the database
		@var UnitClass: Class of the new unit (e.g. Ship, House)
		@return: returnes a unit of the type specified by UnitClass
		"""
		unit = UnitClass(self.view.model, str(id), layer, self)
		self.instance_to_unit[unit.object.getFifeId()] = unit
		unit.start()
		return unit

	def get_tiles_in_radius(self, layer, radius, start_loc):
		"""Returns a list of instances in the radius on the specified layer.
		@var layer: fife.Layer the instances are present on.
		@var radius: int radius that is to be used.
		@var start_loc: fife.Location startpoint.
		@return: list of fife.Instances in the radius arround (startx,starty)."""
		list = []
		generator = (inst for inst in layer.getInstances() if math.fabs(int(inst.getLocation().getMapDistanceTo(start_loc))) <= radius)
		self.view.renderer['InstanceRenderer'].removeAllOutlines()
		for item in generator:
			list.append(item)
			# This is for testing purposes only, should later be done by an own funktion.
			self.view.renderer['InstanceRenderer'].addOutlined(item, 0, 0, 0, 2)
		return list

	def in_radius(self, location_a, location_b, radius):
		"""Checks whether location_b is an radius of location_a.
		@var location_a, location_b: fife.Location
		@var radius: int radius
		@return: boolean whether location_b is in radius of location_a
		"""
		if int(location_a.getMapDistanceTo(location_b)) <= radius:
			return True
		else:
			return False

	def get_instance(self, layer, x, y):
		"""Returns the first instance found on the layer at gridpoint (x,y).
		@var layer: fife.Layer to look on.
		@var x,y: float grid coordinates
		@return: fife.Instance if an Instance is found, else returns None"""
		instances = layer.getInstances()
		inst = (inst for inst in instances if int(inst.getLocation().getExactLayerCoordinatesRef().x) is x and int(inst.getLocation().getExactLayerCoordinatesRef().y is y)).next()
		if inst:
			return inst
		else:
			return None
