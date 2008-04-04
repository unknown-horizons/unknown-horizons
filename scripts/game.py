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

_MODE_COMMAND, _MODE_BUILD = xrange(2)

class Game(EventListenerBase):
    """Game class represents the games main ingame view and controls cameras and map loading."""
    
    def __init__(self, engine, mapfile):
        """@var engine: fife game engine
        @var mapfile: string with the mapfile path
        """
        super(Game, self).__init__(engine, regMouse=True, regKeys=True)
        self.engine = engine
        self.eventmanager = engine.getEventManager()
        self.model = engine.getModel()
        self.metamodel = self.model.getMetaModel()
        self.instance_to_unit = {}
        self.cam = None # main camera

        self.selected_instance = None

        self.human_player = None
        self.players = {}
        self.mode = _MODE_COMMAND
        self.layers = {}
        self.house = None

        #temp var for build testing purposes
        self.num = 0

        self.loadmap(mapfile) # load the map
        self.creategame()

    def loadmap(self, mapfile): 
        """Loads a map.
        @var mapfile: string with the mapfile path
        @var engine: fife game engine
        """
        self.map = loadMapFile(mapfile, self.engine)

    def creategame(self):
        """Initialises rendering, creates the camera and sets it's position."""

        self.layers['water'] = self.map.getLayers("id", "layer1")[0]
        self.layers['land'] = self.map.getLayers("id", "layer2")[0]
        self.layers['units'] = self.map.getLayers("id", "layer3")[0]

        self.human_player = Player('Arthus') # create a new player, which is the human player
        self.players[self.human_player.name] = self.human_player


        #temporary ship creation, should be done automatically in later releases
        ship = self.create_unit(self.layers['land'], 'SHIP', Ship)
        ship.name = 'Matilde'
        self.human_player.ships[ship.name] = ship # add ship to the humanplayer

        ship = self.create_unit(self.layers['land'], 'SHIP2', Ship)
        ship.name = 'Columbus'
        self.human_player.ships[ship.name] = ship # add ship to the humanplayer
        

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
        

    def create_instance(self, layer, objectID, id, x, y, z=0):
        """Creates a new instance on the map
        @var layer: layer the instance is created on
        @var objectID: str representing the object
        @var id: str with the object id
        @var x, y, z: int coordinates for the new instance
        """
        query = self.metamodel.getObjects('id', str(objectID))
        if len(query) != 1: 
            print(''.join([str(len(query)), ' objects found with identifier ', str(objectID), '.']))
        object = query[0]
        inst = layer.createInstance(object, fife.ExactModelCoordinate(x,y,z), str(id))
        fife.InstanceVisual.create(inst)
        return inst
    
    def create_unit(self, layer, objectID, UnitClass):
        """Creates a new unit an the specified layer 
        @var layer: fife.Layer the unit is to be created on
        @var objectID: str containing the object's id
        @var UnitClass: Class of the new unit (e.g. Ship, House)
        @return: returnes a unit of the type specified by UnitClass
        """
        unit = UnitClass(self.model, objectID, layer)
        self.instance_to_unit[unit.object.getFifeId()] = unit
        unit.start()
        return unit


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
        camera = self.view.getCamera("main")
        loc = camera.getLocation()
        cam_scroll = loc.getExactLayerCoordinates()
        if xdir != 0:
            cam_scroll.x += 0.1*xdir*(2/camera.getZoom()) * math.cos(camera.getRotation()/180.0 * math.pi)
            cam_scroll.y += 0.1*xdir*(2/camera.getZoom()) * math.sin(camera.getRotation()/180.0 * math.pi)
        if ydir != 0:
            cam_scroll.x += 0.1*ydir*(2/camera.getZoom()) * math.sin(-camera.getRotation()/180.0 * math.pi);
            cam_scroll.y += 0.1*ydir*(2/camera.getZoom()) * math.cos(-camera.getRotation()/180.0 * math.pi);
        loc.setExactLayerCoordinates(cam_scroll)
        camera.setLocation(loc)

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
            inst = self.create_instance(self.layers['units'], "tent", '', 4, 10)
            self.num += 1
            inst.set("name", "zelt"+str(self.num))
            self.selected_instance = self.create_unit(self.layers['units'], "zelt"+str(self.num), House)
        elif keystr == 'c':
            r = self.cam.getRenderer('CoordinateRenderer')
            r.setEnabled(not r.isEnabled())
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
        #print evt.getButton()
        zoom = self.cam.getZoom() / 0.875
        if(zoom > 1):
            zoom = 1
        #print "zoom: ", zoom
        self.cam.setZoom(zoom)

    def mouseWheelMovedDown(self, evt):
        #print evt.getButton()
        zoom = self.cam.getZoom() * 0.875
        if(zoom < 0.25):
            zoom = 0.25
        #print "zoom: ", zoom
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
