from game.world.building.building import *
import game.main

class Build(object):
	"""Command class that builds an object."""
	def __init__(self, building, x, y, instance = None):
		"""Create the command
		@var object_id: int objects id.
		@var x,y: int coordinates where the object is to be built.
		"""
		self.building = building.id
		self.instance = None if instance == None else instance.getId()
		self.x = int(x)
		self.y = int(y)

	def __call__(self, issuer):
		"""Execute the command
		@var issuer: the issuer of the command
		"""
		game.main.game.world.buildings.append(game.main.game.entities.buildings[self.building](self.x, self.y, issuer, game.main.game.view.layers[1].getInstance(self.instance) if self.instance != None and issuer == game.main.game.world.player else None))
		# TODO: Add building to players/settlements
