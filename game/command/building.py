from game.world.building.building import *
class Build:
	"""Command class that builds an object.
	@var object_id: int objects id.
	@var x,y: float coordinates where the object is to be built.
	"""
	def __init__(self, object_id, x, y, player_id):
		self.object_id = object_id
		self.x = x
		self.y = y
		self.player_id = player_id

	def __call__(self, game, **trash):
		"""__call__() gets called by the manager.
		@var game: main game Session instance.
		"""
		object_class = getBuildingClass(self.object_id)
		object_class.object = game.create_instance(game.layers['units'], game.datasets['building'], self.object_id, self.x, self.y)
		game.instance_to_unit[object_class.object.getFifeId()] = object_class
		# TODO: Add building to players/settlements
