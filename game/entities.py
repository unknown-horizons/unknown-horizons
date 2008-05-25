from game.world.building import BuildingClass
from game.world.units import UnitClass
from game.world.ground import GroundClass
import game.main

class Entities(object):
	def __init__(self):
		self._instances = {}
		self._instances_id = 0

		self.grounds = {}
		for (ground_id,) in game.main.db.query("SELECT rowid FROM data.ground").rows:
			self.grounds[ground_id] = GroundClass(ground_id)

		self.buildings = {}
		for (building_id,) in game.main.db.query("SELECT rowid FROM data.building").rows:
			self.buildings[building_id] = BuildingClass(building_id)

		self.units = {}
		for (unit_id,) in game.main.db.query("SELECT rowid FROM data.unit").rows:
			self.units[unit_id] = UnitClass(unit_id)

	def registerInstance(self, instance):
		id = self._instances_id
		self._instances[id] = instance
		self._instances_id += 1
		return str(id)

	def getInstance(self, id):
		return self._instances[int(id)]
