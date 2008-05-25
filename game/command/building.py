from game.world.building.building import *
import game.main

class Build(object):
	"""Command class that builds an object.
	@var object_id: int objects id.
	@var x,y: float coordinates where the object is to be built.
	"""
	def __init__(self, object_id, x, y, player_id):
		self.object_id = object_id
		self.x = x
		self.y = y
		self.player_id = player_id

	def __call__(self, issuer):
		"""__call__() gets called by the manager.
		@var issuer: the issuer of the command
		"""
		object_class = getBuildingClass(self.object_id)
		object_class.object = game.main.game.create_instance(game.main.game.view.layers[2], 'building', self.object_id, self.x, self.y)
		game.main.game.instance_to_unit[object_class.object.getFifeId()] = object_class
		# TODO: Add building to players/settlements
