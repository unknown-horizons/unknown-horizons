from cursortool import CursorTool
from building.building import *

import fife

"""
Represents a dangling tool after a building was selected from the list.
Builder visualizes if and why a building can not be built under the cursor position.
"""

class BuildingTool(CursorTool):
    "@param building_id: rowid of the selected building type"
    "@param island: If building from a ship context, the building should be restricted to the closest island"
    
    def __init__(self,  game,  building_id,  island = None):
        print "created buildingtool"
        CursorTool.__init__(self,  game.eventmanager)
        
        self.game = game
        self.island = island
        
        self._class = getBuildingClass(building_id)
        
        #TODO: Use a new preview layer
        
        self.previewInstance = game.create_instance(game.layers['units'],  game.datasets['building'],  building_id,  10,  10,  0)
        
    def __del__(self):
        self.game.layers['units'].deleteInstance(self.previewInstance)
        CursorTool.__del__(self)
        

    def mouseMoved(self,  evt):
         pt = fife.ScreenPoint(evt.getX(), evt.getY())
         target_mapcoord = self.game.cam.toMapCoordinates(pt, False)
         target_mapcoord.x = int(target_mapcoord.x)
         target_mapcoord.y = int(target_mapcoord.y)
         target_mapcoord.z = 0
         l = fife.Location(self.game.layers['units'])
         l.setMapCoordinates(target_mapcoord)
         self.previewInstance.setLocation(l)
         target_mapcoord.x = target_mapcoord.x + 1
         l.setMapCoordinates(target_mapcoord)
         self.previewInstance.setFacingLocation(l)
         evt.consume()
         
         try:
            cost = self._class.calcBuildingCost()
            print "Building possible! Cost: " + str(cost)
            # if cost < depot(nearest_island):
            color = (255,  255,  0)
            # else: color = (255, 255, 0) * blink
         except BlockedError:
            # TODO: change to real building exception
            color = (255,  0,  0)
         
         self.game.outline_renderer.addOutlined(self.previewInstance,  255,  255,  0,  5)
         
    def mousePressed(self,  evt):
        if fife.MouseEvent.RIGHT == evt.getButton():
            self.game.cursor = None
        elif fife.MouseEvent.LEFT == evt.getButton():
            pass
            
        evt.consume()
        
