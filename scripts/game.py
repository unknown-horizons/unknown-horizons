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
from loaders import loadMapFile
from eventlistenerbase import EventListenerBase
from units.ship import Ship
from units.house import House
from player import Player
from dbreader import DbReader

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
        self.db_static = DbReader('statics.sqlite')

        self.selected_instance = None

        self.human_player = None
        self.players = {}
        self.mode = _MODE_COMMAND
        self.layers = {}
        self.house = None

        #temp var for build testing purposes
        self.num = 0

        self.loadmap(map) # load the map
        self.creategame()

    def __del__(self):
        super(Game, self).__del__()
        self.model.deleteMap(self.map)
        self.metamodel.deleteDatasets()
        self.view.clearCameras()

    def loadmap(self, map): 
        """Loads a map.
        @var map: string with the mapfile path.
        """
        self.main.db.query("attach ? as map", (map));
        self.map = self.model.createMap("map")

        self.datasets = {}
        self.datasets['ground']=self.metamodel.createDataset("ground") # Dataset for ground tiles
        self.datasets['object']=self.metamodel.createDataset("object") # Dataset for objects 
        
        for (oid, img) in self.main.db.query("select oid, image_n from data.ground").rows:
            self.create_object(oid, img, self.datasets['ground'])

        for (oid, img, size_x, size_y) in self.main.db.query("select oid, image_n, size_x, size_y from data.object").rows:
            id = self.create_object(oid, img, self.datasets['object'])
            #Fix offset NOTE: only testet with the tent, probably needs some adjustment
            pool = self.engine.getImagePool()
            image = pool.getImage(id)
            image.setXShift(image.getWidth()/2-16)
            image.setYShift(0)
        cellgrid = fife.SquareGrid(False)
        cellgrid.thisown = 0
        cellgrid.setRotation(0)
        cellgrid.setXScale(1)
        cellgrid.setYScale(1)
        cellgrid.setXShift(0)
        cellgrid.setYShift(0)
        self.map.createLayer("layer1", cellgrid)
        self.map.createLayer("layer2", cellgrid)
        self.map.createLayer("layer3", cellgrid).setPathingStrategy(fife.CELL_EDGES_ONLY)
        for (island, offset_x, offset_y) in self.main.db.query("select island, x, y from map.islands").rows:
            self.main.db.query("attach ? as island", (str(island)));
            for (x, y, ground) in self.main.db.query("select x, y, ground_id from island.ground").rows:
                if ground == 7 or ground == 11: #create water objects on the water layer
                    fife.InstanceVisual.create(self.map.getLayers("id", "layer1")[0].createInstance(self.datasets['ground'].getObjects('id', str(int(ground)))[0], fife.ExactModelCoordinate(int(x) + int(offset_x), int(y) + int(offset_y), 0), ''))
                else: #put everything else on the land layer
                    fife.InstanceVisual.create(self.map.getLayers("id", "layer2")[0].createInstance(self.datasets['ground'].getObjects('id', str(int(ground)))[0], fife.ExactModelCoordinate(int(x) + int(offset_x), int(y) + int(offset_y), 0), ''))
            self.main.db.query("detach island");

        cam = self.engine.getView().addCamera("main", self.map.getLayers("id", "layer2")[0], fife.Rect(0, 0, self.main.settings.ScreenWidth, self.main.settings.ScreenHeight), fife.ExactModelCoordinate(0,0,0))
        
        cam.setCellImageDimensions(32, 16)
        cam.setRotation(45.0)
        cam.setTilt(60.0)
        cam.setZoom(1)

    def creategame(self):
        """Initialises rendering, creates the camera and sets it's position."""

        self.layers['water'] = self.map.getLayers("id", "layer1")[0]
        self.layers['land'] = self.map.getLayers("id", "layer2")[0]
        self.layers['units'] = self.map.getLayers("id", "layer3")[0]

        self.human_player = Player('Arthus') # create a new player, which is the human player
        self.players[self.human_player.name] = self.human_player


        #temporary ship creation, should be done automatically in later releases
        #ship = self.create_unit(self.layers['land'], 'SHIP', 'mainship_ani' , Ship)
        #ship.name = 'Matilde'
        #self.human_player.ships[ship.name] = ship # add ship to the humanplayer

        #ship = self.create_unit(self.layers['land'], 'SHIP2', 'mainship_ani', Ship)
        #ship.name = 'Columbus'
        #self.human_player.ships[ship.name] = ship # add ship to the humanplayer
        

        self.view = self.engine.getView()
        self.view.resetRenderers()
        self.cam = self.view.getCamera("main")
        self.set_cam_position(5.0, 5.0, 0.0)

        renderer = fife.FloatingTextRenderer.getInstance(self.cam)
        renderer = self.cam.getRenderer('QuadTreeRenderer')
        renderer.setEnabled(True)
        renderer.clearActiveLayers() 
        renderer = self.cam.getRenderer('CoordinateRenderer')
        renderer.clearActiveLayers()
        renderer.addActiveLayer(self.layers['land'])

    def create_object(self, oid, img, dataset):
        """Creates a new dataset object, that can later be used on the map
        @var oid: the object oid in the database
        @var img: str representing the object's image
        @var dataset: the dataset the object is to be created on
        """
        obj = dataset.createObject(str(oid), None)
        fife.ObjectVisual.create(obj)
        id = self.engine.getImagePool().addResourceFromFile(str(img))
        obj.get2dGfxVisual().addStaticImage(0, id)
        return id
        

    def create_instance(self, layer, objectID, id, x, y, z=0):
        """Creates a new instance on the map
        @var layer: layer the instance is created on
        @var objectID: str representing the object
        @var id: str with the object id
        @var x, y, z: int coordinates for the new instance
        """
        query = self.datasets['object'].getObjects('id', str(id))
        if len(query) != 1: 
            print(''.join([str(len(query)), ' objects found with id ', str(7), '.']))
        object = query[0]
        inst = layer.createInstance(object, fife.ExactModelCoordinate(x,y,z), str(id))
        fife.InstanceVisual.create(inst)
        return inst
    
    def create_unit(self, layer, objectName, id, UnitClass):
        """Creates a new unit an the specified layer 
        @var layer: fife.Layer the unit is to be created on
        @var id: str containing the object's id
        @var UnitClass: Class of the new unit (e.g. Ship, House)
        @return: returnes a unit of the type specified by UnitClass
        """
        unit = UnitClass(self.model, id, layer)
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
        layer = self.map.getLayers("id", "layer1")[0]
        loc = fife.Location(layer)
        loc.setExactLayerCoordinates(fife.ExactModelCoordinate(x, y, z))
        self.cam.setLocation(loc)

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
            cam_scroll.x += 0.1*ydir*(2/self.cam.getZoom()) * math.sin(-self.cam.getRotation()/180.0 * math.pi);
            cam_scroll.y += 0.1*ydir*(2/self.cam.getZoom()) * math.cos(-self.cam.getRotation()/180.0 * math.pi);
        loc.setExactLayerCoordinates(cam_scroll)
        self.cam.setLocation(loc)

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
        # FIXME: Removed build option, as it does not work.
        elif keystr == 'b' and self.mode is _MODE_COMMAND:
            self.mode = _MODE_BUILD
            inst = self.create_instance(self.layers['units'], "tent", '2', 4, 10)
            self.num += 1
            self.selected_instance = self.create_unit(self.layers['units'], "zelt"+str(self.num), '2', House)
        elif keystr == 'c':
            r = self.cam.getRenderer('CoordinateRenderer')
            r.setEnabled(not r.isEnabled())
        elif keystr == 'q':
            self.main.quit()
        if keystr == 't':
            r = self.cam.getRenderer('GridRenderer')
            r.setEnabled(not r.isEnabled())

    def mousePressed(self, evt):
        clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
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
            print self.build_check(target_mapcoord, self.selected_instance)
