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

from game.gui.eventlistenerbase import EventListenerBase
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

class Game(EventListenerBase):
	"""Game class represents the games main ingame view and controls cameras and map loading."""
	def __init__(self):
		pass

	def init(self, map):
		"""
		@var map: string with the mapfile path
		"""
		super(Game, self).__init__(regKeys=True)

		#
		# Engine specific variables
		#
		self.eventmanager = game.main.fife.engine.getEventManager()
		self.model = game.main.fife.engine.getModel()

		#
		# Map and Instance specific variables
		#
		self.island_uid = 0     # Unique id used for islands.
		self.islands = {}
		self.uid = 0            # Unique id used to create unique ids for instances.
		self.layers = {}
		self.selected_instance = None
		self.instance_to_unit = {}

		#
		# Player related variable
		#
		self.human_player = None
		self.players = {0 : None}

		#
		# Camera related variables
		#
		#self.overview = None    # Overview camera
		self.view = None
		self.outline_renderer = None

		#
		# Gui related variables
		#
		self.ingame_gui = None
		self.keylistener = IngameKeyListener(game.main.fife.engine, self)
		self.cursor = None
		self.set_selection_mode()

		#
		# Other variables
		#
		self.timer = Timer(16)
		self.manager = SPManager()
		self.scheduler = Scheduler()
		self.timer.add_call(self.scheduler.tick)

		#
		# Beginn map creation
		#

		building.initBuildingClasses()

		self.loadmap(map)
		self.creategame()

	def __del__(self):
		super(Game, self).__del__()
		self.model.deleteMap(self.map)
		self.engine.getView().clearCameras()
		self.ticker = None

	def loadmap(self, map):
		"""Loads a map.
		@var map: string with the mapfile path.
		"""
		game.main.db.query("attach ? as map", (map))
		self.map = self.model.createMap("map")

		self.create_object("blocker", "content/gfx/dummies/transparent.png", "content/gfx/dummies/transparent.png", "content/gfx/dummies/transparent.png", "content/gfx/dummies/transparent.png", "content/gfx/dummies/transparent.png", "blocker")
		#todo...
		for (oid, multi_action_or_animated) in game.main.db.query("SELECT id, max(actions_and_images) > 1 AS multi_action_or_animated FROM ( SELECT ground.oid as id, action.animation as animation, count(*) as actions_and_images FROM ground LEFT JOIN action ON action.ground = ground.oid LEFT JOIN animation ON action.animation = animation.animation_id GROUP BY ground.oid, action.rotation ) x GROUP BY id").rows:
			print oid, multi_action_or_animated

		for (oid, image_overview, image_n, image_e, image_s, image_w) in game.main.db.query("select gnd.oid, grp.image_overview, (select file from data.animation where animation_id = (select animation from data.action where ground = gnd.rowid and rotation = 45) order by frame_end limit 1) as image_n, (select file from data.animation where animation_id = (select animation from data.action where ground = gnd.rowid and rotation = 135) order by frame_end limit 1) as image_e, (select file from data.animation where animation_id = (select animation from data.action where ground = gnd.rowid and rotation = 225) order by frame_end limit 1) as image_s, (select file from data.animation where animation_id = (select animation from data.action where ground = gnd.rowid and rotation = 315) order by frame_end limit 1) as image_w from data.ground gnd left join data.ground_group grp on gnd.`group` = grp.oid").rows:
			self.create_object(oid, image_overview, image_n, image_e, image_s, image_w, "ground")

		for (oid, image_overview, image_n, image_e, image_s, image_w, size_x, size_y) in game.main.db.query("select oid, 'content/gfx/dummies/overview/object.png', (select file from data.animation where animation_id = (select animation from data.action where object = data.building.rowid and rotation = 45) order by frame_end limit 1) as image_n, (select file from data.animation where animation_id = (select animation from data.action where object = data.building.rowid and rotation = 135) order by frame_end limit 1) as image_e, (select file from data.animation where animation_id = (select animation from data.action where object = data.building.rowid and rotation = 225) order by frame_end limit 1) as image_s, (select file from data.animation where animation_id = (select animation from data.action where object = data.building.rowid and rotation = 315) order by frame_end limit 1) as image_w, size_x, size_y from data.building").rows:
			self.create_object(oid, image_overview, image_n, image_e, image_s, image_w, "building", size_x, size_y)

		cellgrid = fife.SquareGrid(False)
		cellgrid.thisown = 0
		cellgrid.setRotation(0)
		cellgrid.setXScale(1)
		cellgrid.setYScale(1)
		cellgrid.setXShift(0)
		cellgrid.setYShift(0)

		self.layers['water'] = self.map.createLayer("layer1", cellgrid)
		self.layers['land'] = self.map.createLayer("layer2", cellgrid)
		self.layers['units'] = self.map.createLayer("layer3", cellgrid)
		self.layers['units'].setPathingStrategy(fife.CELL_EDGES_ONLY)

		min_x, min_y, max_x, max_y = 0, 0, 0, 0
		for (island, offset_x, offset_y) in game.main.db.query("select island, x, y from map.islands").rows:
			game.main.db.query("attach ? as island", (str(island)))
			self.islands[self.island_uid]=Island(self.island_uid)
			cur_isl = self.islands[self.island_uid]
			for (x, y, ground, layer) in game.main.db.query("select i.x, i.y, i.ground_id, g.ground_type_id from island.ground i left join data.ground c on c.oid = i.ground_id left join data.ground_group g on g.oid = c.`group`").rows:
				inst = self.create_instance(self.layers['land'], 'ground', str(int(ground)), int(x) + int(offset_x), int(y) + int(offset_y), 0)
				cur_isl.add_tile(inst)
				min_x = int(x) + int(offset_x) if min_x is 0 or int(x) + int(offset_x) < min_x else min_x
				max_x = int(x) + int(offset_x) if max_x is 0 or int(x) + int(offset_x) > max_x else max_x
				max_y = int(y) + int(offset_y) if max_y is 0 or int(y) + int(offset_y) > max_y else max_y
				min_y = int(y) + int(offset_y) if min_y is 0 or int(y) + int(offset_y) < min_y else min_y
			self.island_uid += 1
			game.main.db.query("detach island")

		for x in range(min_x-10, (max_x+11)): # Fill map with water tiles + 10 on each side
			for y in range(min_y-10, max_y+11):
				inst = self.create_instance(self.layers['water'], 'ground', str(int(13)), int(x), int(y), 0)

		self.view = View(self.map.getLayer("layer1"), (((max_x - min_x) / 2.0), ((max_y - min_y) / 2.0), 0.0))

		#self.overview = self.engine.getView().addCamera("overview", self.map.getLayers("id", "layer1")[0], fife.Rect(0, self.main.settings.ScreenHeight - 200 if False else 0, 200, 200), fife.ExactModelCoordinate((((max_x - min_x) / 2.0) + 5), ((max_y - min_y) / 2.0), 0.0))
		#self.overview.setCellImageDimensions(2, 2)
		#self.overview.setRotation(0.0)
		#self.overview.setTilt(0.0)
		#self.overview.setZoom(100.0 / (1 + max(max_x - min_x, max_y - min_y)))
		print self.model.getNamespaces()

	def set_selection_mode(self):
		"""Sets the game into selection mode."""
		self.cursor = SelectionTool(self)

	def creategame(self):
		"""Initialises rendering, creates the camera and sets it's position."""

		#create a new player, which is the human player
		self.human_player = Player(1 ,'Arthus')
		self.players[self.human_player.name] = self.human_player

		self.ingame_gui = IngameGui()
		self.ingame_gui.status_set('gold','10000')

		#temporary ship creation, should be done automatically in later releases
		self.create_object('99', "content/gfx/dummies/overview/object.png", "content/gfx/sprites/ships/mainship/mainship1.png", "content/gfx/sprites/ships/mainship/mainship3.png", "content/gfx/sprites/ships/mainship/mainship5.png", "content/gfx/sprites/ships/mainship/mainship7.png", "building", 1, 1)
		tempid = self.uid
		inst = self.create_instance(self.layers['land'], 'building', '99', 25, 25)
		ship = self.create_unit(self.layers['land'], str(tempid), 99, Ship)
		ship.name = 'Matilde'
		#self.human_player.ships[ship.name] = ship # add ship to the humanplayer

		game.main.fife.engine.getView().resetRenderers()

		renderer = self.view.cam.getRenderer('CoordinateRenderer')
		renderer.clearActiveLayers()
		renderer.addActiveLayer(self.layers['land'])

		self.outline_renderer = fife.InstanceRenderer.getInstance(self.view.cam)

	def create_object(self, oid, image_overview, image_n, image_e, image_s, image_w, namespace, size_x = 1, size_y = 1):
		"""Creates a new model object, that can later be used on the map
		@var oid: the object oid in the database.
		@var image_overview, image_n, image_e, image_s, image_w: str representing the object's images.
        @var size_x: the x-size of the object in grid's.
		@var size_y: the y-size of the object in grid's.
        @var namespace: namespace the object belongs to.
		"""
		obj = self.model.createObject(str(oid), namespace)
		fife.ObjectVisual.create(obj)
		visual = obj.get2dGfxVisual()
		pool = game.main.fife.engine.getImagePool()

		img = pool.addResourceFromFile(str(image_overview))
		visual.addStaticImage(0, img)
		visual.addStaticImage(90, img)
		visual.addStaticImage(180, img)
		visual.addStaticImage(270, img)

		img = pool.addResourceFromFile(str(image_n))
		visual.addStaticImage(45, img)
		img = pool.getImage(img)
		img.setXShift(0)#16 - 16 * size_y
		img.setYShift(-(img.getHeight() - 16) / 2)

		img = pool.addResourceFromFile(str(image_e))
		visual.addStaticImage(135, img)
		img = pool.getImage(img)
		img.setXShift(0)
		img.setYShift(0)

		img = pool.addResourceFromFile(str(image_s))
		visual.addStaticImage(225, img)
		img = pool.getImage(img)
		img.setXShift(0)
		img.setYShift(0)

		img = pool.addResourceFromFile(str(image_w))
		visual.addStaticImage(315, img)
		img = pool.getImage(img)
		img.setXShift(0)
		img.setYShift(0)

		return obj

	def create_instance(self, layer, namespace, id, x, y, z=0):
		"""Creates a new instance on the map
		@var layer: layer the instance is created on
        @var namespace: string namespace the object is present in
		@var id: str with the object id
		@var x, y, z: int coordinates for the new instance
		"""
		query = self.model.getObject(str(id), namespace)
		if query == 0:
			print('Object not found with id ', str(id), '!')
		object = query
		inst = layer.createInstance(object, fife.ExactModelCoordinate(x,y,z), str(self.uid))
		self.uid += 1
		fife.InstanceVisual.create(inst)
		return inst

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
		unit = UnitClass(self.model, str(id), layer, self)
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
		self.outline_renderer.removeAllOutlines()
		for item in generator:
			list.append(item)
			# This is for testing purposes only, should later be done by an own funktion.
			self.outline_renderer.addOutlined(item, 0, 0, 0, 2)
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
