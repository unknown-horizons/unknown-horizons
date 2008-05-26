import fife
import game.main

class Move(object):
	"""Command class that moves a unit.
	@var unit_fife_id: int FifeId of the unit that is to be moved.
	@var x,y: float coordinates where the unit is to be moved.
	@var layer: the layer the unit is present on.
	"""
	def __init__(self, unit, x, y):
		self.unit = unit._instance.getId()
		self.x = int(x)
		self.y = int(y)

	def __call__(self, issuer):
		"""__call__() gets called by the manager.
		@var issuer: the issuer of the command
		"""
		game.main.game.entities.getInstance(self.unit).move(self.x, self.y)
