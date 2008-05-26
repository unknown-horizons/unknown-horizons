from cursortool import CursorTool
from selectiontool import SelectionTool
from game.world.building.building import *
from game.command.building import Build

import fife
import game.main

"""
Represents a dangling tool after a building was selected from the list.
Builder visualizes if and why a building can not be built under the cursor position.
"""

class BuildingTool(CursorTool):
	"@param building_id: rowid of the selected building type"
	"@param island: If building from a ship, restrict to range of ship"

	def __init__(self, building_id, ship = None):
		print "created buildingtool"
		super(BuildingTool, self).__init__()

		self.ship = ship
		self.building_id = building_id

		self._class = game.main.game.entities.buildings[building_id]

		self.previewInstance = self._class.createInstance(-100, -100)

	def _buildCheck(self,  position):
		# TODO: Return more detailed error descriptions than a boolean
		try:
			cost = self._class.calcBuildingCost(game.main.game.view.layers[0],  game.main.game.view.layers[1],  position)
			# TODO: implement cost checking
			# if cost < depot(nearest_island or ship):
		except BlockedError:
			return False

		if self.ship:
			shippos = self.ship._instance.getLocation().getMapCoordinates()
			distance = (shippos - position).length()
			if distance > 10:
				return False
		return True

	def mouseMoved(self,  evt):
		pt = fife.ScreenPoint(evt.getX(), evt.getY())
		target_mapcoord = game.main.game.view.cam.toMapCoordinates(pt, False)
		target_mapcoord.x = int(target_mapcoord.x)
		target_mapcoord.y = int(target_mapcoord.y)
		target_mapcoord.z = 0
		l = fife.Location(game.main.game.view.layers[1])
		l.setMapCoordinates(target_mapcoord)
		self.previewInstance.setLocation(l)
		target_mapcoord.x = target_mapcoord.x + 1
		l.setMapCoordinates(target_mapcoord)
		self.previewInstance.setFacingLocation(l)
		evt.consume()

		can_build = self._buildCheck(target_mapcoord)
		if can_build: color = (255,  255,  0)
		else: color = (255,  0,  0)

		game.main.game.view.renderer['InstanceRenderer'].addOutlined(self.previewInstance,  color[0],  color[1],  color[2],  5)

	def mousePressed(self,  evt):
		if fife.MouseEvent.RIGHT == evt.getButton():
			game.main.game.cursor = SelectionTool()
			game.main.game.view.layers[1].deleteInstance(self.previewInstance)
		elif fife.MouseEvent.LEFT == evt.getButton():
			pt = fife.ScreenPoint(evt.getX(), evt.getY())
			mapcoord = game.main.game.view.cam.toMapCoordinates(pt, False)
			mapcoord.x = int(mapcoord.x)
			mapcoord.y = int(mapcoord.y)
			mapcoord.z = 0
			if self._buildCheck(mapcoord):
				game.main.game.manager.execute(Build(self._class, mapcoord.x, mapcoord.y, self.previewInstance))
				game.main.game.cursor = SelectionTool()
		evt.consume()
