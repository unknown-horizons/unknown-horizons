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

class Game:
    """Game class represents the games main ingame view and controls cameras and map loading."""
    
    def __init__(self, engine, mapfile):
        """@var engine: fife game engine
        @var mapfile: string with the mapfile path
        """
        self.engine = engine
        
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
        self.view = self.engine.getView()
        self.view.resetRenderers()
        self.cam = self.view.getCamera("main")
        self.set_cam_position(0.0, 0.0, 0.0)
        renderer = self.cam.getRenderer('QuadTreeRenderer')
        renderer.setEnabled(True)
        renderer.clearActiveLayers()

    def set_cam_position(self, x, y, z):
        """Sets the camera position
        @var pos: tuple with coordinates(x.x,x.x,x.x) to set the camera to.
        """
        layer = self.map.getLayers("id", "landLayer")[0]
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



