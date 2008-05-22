from cursortool import CursorTool
from game.world.building.building import *
from game.command.building import Build

import fife

"""
Represents a dangling tool after a building was selected from the list.
Builder visualizes if and why a building can not be built under the cursor position.
"""

class BuildingTool(CursorTool):
	"@param building_id: rowid of the selected building type"
	"@param island: If building from a ship, restrict to range of ship"

	def __init__(self,  game,  building_id,  ship = None):
		print "created buildingtool"
		CursorTool.__init__(self,  game.eventmanager)

		self.game = game
		self.ship = ship
		self.building_id = building_id

		self._class = getBuildingClass(building_id)

		#TODO: Use a new preview layer

		self.previewInstance = game.create_instance(game.layers['units'],  'building',  building_id,  -100,  -100,  0)

	def __del__(self):
		self.game.layers['units'].deleteInstance(self.previewInstance)
		CursorTool.__del__(self)

	def _buildCheck(self,  position):
		# TODO: Return more detailed error descriptions than a boolean
		try:
			cost = self._class.calcBuildingCost(self.game.layers['land'],  self.game.layers['units'],  position)
			# TODO: implement cost checking
			# if cost < depot(nearest_island or ship):
		except BlockedError:
			return False

		if self.ship:
			shippos = self.ship.object.getLocation().getMapCoordinates()
			distance = (shippos - position).length()
			print distance
			if distance > 10:
				return False
		return True

	def mouseMoved(self,  evt):
		pt = fife.ScreenPoint(evt.getX(), evt.getY())
		target_mapcoord = self.game.view.cam.toMapCoordinates(pt, False)
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

		can_build = self._buildCheck(target_mapcoord)
		print can_build
		if can_build: color = (255,  255,  0)
		else: color = (255,  0,  0)

		self.game.outline_renderer.addOutlined(self.previewInstance,  color[0],  color[1],  color[2],  5)

	def mousePressed(self,  evt):
		if fife.MouseEvent.RIGHT == evt.getButton():
			self.game.set_selection_mode()
		elif fife.MouseEvent.LEFT == evt.getButton():
			pt = fife.ScreenPoint(evt.getX(), evt.getY())
			mapcoord = self.game.view.cam.toMapCoordinates(pt, False)
			mapcoord.x = int(mapcoord.x)
			mapcoord.y = int(mapcoord.y)
			mapcoord.z = 0
			if self._buildCheck(mapcoord):
				self.game.manager.execute(Build(self.building_id, mapcoord.x, mapcoord.y, self.game.human_player.id))
				self.game.set_selection_mode()
		evt.consume()
