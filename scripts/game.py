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
import math
import fife
import pychan
from loaders import loadMapFile
from eventlistenerbase import EventListenerBase
from units.ship import Ship
from units.house import House
from player import Player
from dbreader import DbReader
from ingamegui import IngameGui
import timermanager
import random

_MODE_COMMAND, _MODE_BUILD = xrange(2)

class Game(EventListenerBase):
    """Game class represents the games main ingame view and controls cameras and map loading."""

    def __init__(self, main, map):
        """@var main: parant Openanno instance
        @var map: string with the mapfile path
        """
        self.main = main
        engine = self.main.engine
        super(Game, self).__init__(engine, regMouse=True, regKeys=True)
        self.engine = engine
        self.eventmanager = engine.getEventManager()
        self.model = engine.getModel()
        self.metamodel = self.model.getMetaModel()
        self.instance_to_unit = {}
        self.cam = None # main camera
        self.uid = 0 # openanno intern uid which is used to create unique numbers for instances.

        self.selected_instance = None
        self.human_player = None
        self.players = {}
        self.mode = _MODE_COMMAND
        self.layers = {}
        self.house = None

        #temp var for build testing purposes
        self.timermanager = timermanager.TimerManager() #managers timers
        self.loadmap(map) # load the map
        self.creategame()

    def __del__(self):
        super(Game, self).__del__()
        self.model.deleteMap(self.map)
        self.metamodel.deleteDatasets()
        self.view.clearCameras()
        self.timermanager.stop_all()

    def loadmap(self, map):
        """Loads a map.
        @var map: string with the mapfile path.
        """
        self.main.db.query("attach ? as map", (map))
        self.map = self.model.createMap("map")

        self.datasets = {}
        #dataset for ground tiles
        self.datasets['ground']=self.metamodel.createDataset("ground")
        #dataset for objects
        self.datasets['object']=self.metamodel.createDataset("object")

        self.create_object("blocker", "content/gfx/dummies/transparent.png", "content/gfx/dummies/transparent.png", "content/gfx/dummies/transparent.png", "content/gfx/dummies/transparent.png", "content/gfx/dummies/transparent.png", self.datasets['ground'])
        for (oid, image_overview, image_n, image_e, image_s, image_w) in self.main.db.query("select gnd.oid, grp.image_overview, gnd.image_n, gnd.image_e, gnd.image_s, gnd.image_w from data.ground gnd left join data.ground_group grp on gnd.`group` = grp.oid").rows:
            self.create_object(oid, image_overview, image_n, image_e, image_s, image_w, self.datasets['ground'])

        for (oid, image_overview, image_n, image_e, image_s, image_w, size_x, size_y) in self.main.db.query("select oid, 'content/gfx/dummies/overview/object.png', image_n, image_e, image_s, image_w, size_x, size_y from data.object").rows:
            self.create_object(oid, image_overview, image_n, image_e, image_s, image_w, self.datasets['object'], size_x, size_y)

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

        for (island, offset_x, offset_y) in self.main.db.query("select island, x, y from map.islands").rows:
            self.main.db.query("attach ? as island", (str(island)))
            for (x, y, ground, layer) in self.main.db.query("select i.x, i.y, i.ground_id, g.ground_type_id from island.ground i left join data.ground c on c.oid = i.ground_id left join data.ground_group g on g.oid = c.`group`").rows:
                self.create_instance(self.layers['land'], self.datasets['ground'], str(int(ground)), int(x) + int(offset_x), int(y) + int(offset_y), 0)
            self.main.db.query("detach island")

        self.cam = self.engine.getView().addCamera("main", self.map.getLayers("id", "layer1")[0], fife.Rect(0, 0, self.main.settings.ScreenWidth, self.main.settings.ScreenHeight), fife.ExactModelCoordinate(0,0,0))
        self.cam.setCellImageDimensions(32, 16)
        self.cam.setRotation(45.0)
        self.cam.setTilt(60.0)
        self.cam.setZoom(1)

        self.overview = self.engine.getView().addCamera("overview", self.map.getLayers("id", "layer1")[0], fife.Rect(0, self.main.settings.ScreenHeight - 200 if False else 0, 200, 200), fife.ExactModelCoordinate(0,0,0))
        self.overview.setCellImageDimensions(2, 2)
        self.overview.setRotation(0.0)
        self.overview.setTilt(0.0)
        self.overview.setZoom(1)

    def creategame(self):
        """Initialises rendering, creates the camera and sets it's position."""

        #create a new player, which is the human player
        self.human_player = Player('Arthus')
        self.players[self.human_player.name] = self.human_player

        self.ingame_gui = IngameGui()
        self.ingame_gui.status_set('gold','10000')
        
        #temporary ship creation, should be done automatically in later releases
        #ship = self.create_unit(self.layers['land'], 'SHIP', 'mainship_ani' , Ship)
        #ship.name = 'Matilde'
        #self.human_player.ships[ship.name] = ship # add ship to the humanplayer

        #ship = self.create_unit(self.layers['land'], 'SHIP2', 'mainship_ani', Ship)
        #ship.name = 'Columbus'
        #self.human_player.ships[ship.name] = ship # add ship to the humanplayer

        self.view = self.engine.getView()
        self.view.resetRenderers()
        self.set_cam_position(5.0, 5.0, 0.0)

        renderer = self.cam.getRenderer('CoordinateRenderer')
        renderer.clearActiveLayers()
        renderer.addActiveLayer(self.layers['land'])

    def create_object(self, oid, image_overview, image_n, image_e, image_s, image_w, dataset, size_x = 1, size_y = 1):
        """Creates a new dataset object, that can later be used on the map
        @var oid: the object oid in the database
        @var image_overview, image_n, image_e, image_s, image_w: str representing the object's images
        @var dataset: the dataset the object is to be created on
        @var size_x: the x-size of the object in grid's
        @var size_y: the y-size of the object in grid's
        """
        obj = dataset.createObject(str(oid), None)
        fife.ObjectVisual.create(obj)
        visual = obj.get2dGfxVisual()
        pool = self.engine.getImagePool()

        img = pool.addResourceFromFile(str(image_overview))
        visual.addStaticImage(0, img)
        visual.addStaticImage(90, img)
        visual.addStaticImage(180, img)
        visual.addStaticImage(270, img)

        img = pool.addResourceFromFile(str(image_n))
        visual.addStaticImage(45, img)
        img = pool.getImage(img)
        img.setXShift(16 - 16 * size_y)
        img.setYShift(0)

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

    def create_instance(self, layer, dataset, id, x, y, z=0):
        """Creates a new instance on the map
        @var layer: layer the instance is created on
        @var id: str with the object id
        @var x, y, z: int coordinates for the new instance
        """
        query = dataset.getObjects('id', str(id))
        if len(query) != 1:
            print(''.join([str(len(query)), ' objects found with id ', str(7), '.']))
        object = query[0]
        inst = layer.createInstance(object, fife.ExactModelCoordinate(x,y,z), str(self.uid))
        self.uid += 1
        fife.InstanceVisual.create(inst)
        return inst

    def create_unit(self, layer, id, UnitClass):
        """Creates a new unit an the specified layer
        @var layer: fife.Layer the unit is to be created on
        @var id: str containing the object's id
        @var UnitClass: Class of the new unit (e.g. Ship, House)
        @return: returnes a unit of the type specified by UnitClass
        """
        unit = UnitClass(self.model, str(id), layer, self)
        if UnitClass is House:
            res = self.main.db.query("SELECT * FROM data.object WHERE rowid = ?",id)
            if res.success:
                unit.size_x, unit.size_y = self.main.db.query("SELECT size_x,size_y FROM data.object WHERE rowid = ?",id).rows[0]
                print unit.size_x, unit.size_y
        self.instance_to_unit[unit.object.getFifeId()] = unit
        unit.start()
        return unit

    def build_check(self, point, inst):
        """
        Checkes whether or not a building can be built at the current mouse position.
        @var point: fife.MapPoint where the cursor is currently at.
        @var inst: Object instance that is to be built (must have size_x and size_y set).
        """

        #FIXME: works basically, but will result in problems with unit checking and wrong checks on the lower right side of islands
        def check_inst(layer, point, inst):
            instances = self.cam.getMatchingInstances(self.cam.toScreenCoordinates(point), layer)
            if instances: #Check whether the found instance equals the instance that is to be built.
                if inst.object.getFifeId() == instances[0].getFifeId():
                    instances = instances[1:len(instances)]
            if instances and len(instances) > 0:
                return True
            else:
                return False
        point.x = float(point.x)+0.5
        starty = float(point.y)-0.5
        checkpoint = point
        check = True
        print 'Start check x: ', point.x, ' y: ', starty
        for x in xrange(inst.size_x):
            checkpoint.y = starty
            for y in xrange(inst.size_y):
                print 'Checking x: ', checkpoint.x,' y: ', checkpoint.y
                check = check_inst(self.layers['land'], checkpoint, inst)
                print 'land check:', check
                if check:
                    check = (not check_inst(self.layers['units'], checkpoint, inst))
                    print 'unit check:', check
                else:
                    break
                checkpoint.y += 1
            if not check:
                break
            checkpoint.x += 1
        print 'Finished check'
        return check

    def set_cam_position(self, x, y, z):
        """Sets the camera position
        @var pos: tuple with coordinates(x.x,x.x,x.x) to set the camera to.
        """
        loc = fife.Location(self.layers['water'])
        loc.setExactLayerCoordinates(fife.ExactModelCoordinate(x, y, z))
        self.cam.setLocation(loc)
        self.overview.setLocation(loc)

    def move_camera(self, xdir, ydir):
        """Moves the camera across the screen.
        @var xdir: int representing x direction scroll.
        @var ydir: int representing y direction scroll.
        """
        loc = self.cam.getLocation()
        cam_scroll = loc.getExactLayerCoordinates()
        if xdir != 0:
            cam_scroll.x += 0.1*xdir*(2/self.cam.getZoom()) * math.cos(self.cam.getRotation()/180.0 * math.pi)
            cam_scroll.y += 0.1*xdir*(2/self.cam.getZoom()) * math.sin(self.cam.getRotation()/180.0 * math.pi)
        if ydir != 0:
            cam_scroll.x += 0.1*ydir*(2/self.cam.getZoom()) * math.sin(-self.cam.getRotation()/180.0 * math.pi)
            cam_scroll.y += 0.1*ydir*(2/self.cam.getZoom()) * math.cos(-self.cam.getRotation()/180.0 * math.pi)
        loc.setExactLayerCoordinates(cam_scroll)
        self.cam.setLocation(loc)
        self.overview.setLocation(loc)

    def keyPressed(self, evt):
        keyval = evt.getKey().getValue()
        keystr = evt.getKey().getAsString().lower()
        if keyval == fife.Key.LEFT:
            self.move_camera(-3, 0)
        elif keyval == fife.Key.RIGHT:
            self.move_camera(3, 0)
        elif keyval == fife.Key.UP:
            self.move_camera(0, -3)
        elif keyval == fife.Key.DOWN:
            self.move_camera(0, 3)
        elif keystr == 'b' and self.mode is _MODE_COMMAND:
            self.mode = _MODE_BUILD
            curunique = self.uid
            inst = self.create_instance(self.layers['units'], self.datasets['object'], '2', 4, 10)
            self.selected_instance = self.create_unit(self.layers['units'], curunique, House)
        elif keystr == 'c':
            r = self.cam.getRenderer('CoordinateRenderer')
            r.setEnabled(not r.isEnabled())
        elif keystr == 'r':
            self.cam.setRotation((self.cam.getRotation() + 90) % 360)
        elif keystr == 'q':
            self.__del__()
            self.main.quit()    
        if keystr == 't':
            r = self.cam.getRenderer('GridRenderer')
            r.setEnabled(not r.isEnabled())

    def mousePressed(self, evt):
        clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
        if evt.getX() < 200 and evt.getY() < 200:
            loc = fife.Location(self.layers["water"])
            loc.setExactLayerCoordinates(self.overview.toMapCoordinates(clickpoint, True))
            self.cam.setLocation(loc)
            self.overview.setLocation(loc)
        else:
            if (evt.getButton() == fife.MouseEvent.LEFT):
                if self.mode is _MODE_COMMAND: # standard mode
                    instances = self.cam.getMatchingInstances(clickpoint, self.layers['land'])
                    if instances: #check if clicked point is a unit
                        selected = instances[0]
                        print "selected instance: ", selected.get("name"), selected.getFifeId()
                        if self.selected_instance:
                                self.selected_instance.object.say('') #remove status of last selected unit
                        if selected.getFifeId() in self.instance_to_unit:
                            self.selected_instance = self.instance_to_unit[selected.getFifeId()]
                            self.selected_instance.object.say(str(self.selected_instance.health) + '%', 0) # display health over selected ship
                        else:
                            self.selected_instance = None
                    elif self.selected_instance: # if unit is allready selected, move it
                        if self.selected_instance.type == 'ship':
                            target_mapcoord = self.cam.toMapCoordinates(clickpoint, False)
                            target_mapcoord.z = 0
                            l = fife.Location(self.layers['land'])
                            l.setMapCoordinates(target_mapcoord)
                            self.selected_instance.move(l)
                else:
                    if self.build_check(self.cam.toMapCoordinates(clickpoint), self.selected_instance):
                        self.mode = _MODE_COMMAND
                        self.selected_instance = None
            elif (evt.getButton() == fife.MouseEvent.RIGHT):
                if self.mode is _MODE_COMMAND:
                    if self.selected_instance: #remove unit selection
                        self.selected_instance.object.say('', 0) # remove health display
                        self.selected_instance = None
                else:
                    self.mode = _MODE_COMMAND
                    self.layers['units'].deleteInstance(self.selected_instance.object)
                    self.selected_instance = None

    def mouseWheelMovedUp(self, evt):
        zoom = self.cam.getZoom() / 0.875
        if(zoom > 1):
            zoom = 1
        self.cam.setZoom(zoom)

    def mouseWheelMovedDown(self, evt):
        zoom = self.cam.getZoom() * 0.875
        if(zoom < 0.25):
            zoom = 0.25
        self.cam.setZoom(zoom)

    def mouseMoved(self, evt):
        if self.mode == _MODE_BUILD:
            pt = fife.ScreenPoint(evt.getX(), evt.getY())
            target_mapcoord = self.cam.toMapCoordinates(pt, False)
            target_mapcoord.x = int(target_mapcoord.x)
            target_mapcoord.y = int(target_mapcoord.y)
            target_mapcoord.z = 0
            l = fife.Location(self.layers['units'])
            l.setMapCoordinates(target_mapcoord)
            self.selected_instance.move(l)
            #print self.build_check(target_mapcoord, self.selected_instance)
