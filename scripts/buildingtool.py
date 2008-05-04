from cursortool import CursorTool
from building.building import getBuildingClass

"""
Represents a dangling tool after a building was selected from the list.
Builder visualizes if and why a building can not be built under the cursor position.
"""

class BuildingTool(CursorTool):
    "@param building_id: rowid of the selected building type"
    "@param island: If building from a ship context, the building should be restricted to the closest island"
    
    def __init__(self,  game,  building_id,  island = None):
        CursorTool.__init__(self,  game.eventmanager)
        self.island = island
        
        self._class = getBuildingClass(building_id)
