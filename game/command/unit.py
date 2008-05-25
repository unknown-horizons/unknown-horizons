import fife
import game.main

class Move(object):
	"""Command class that moves a unit.
	@var unit_fife_id: int FifeId of the unit that is to be moved.
	@var x,y: float coordinates where the unit is to be moved.
	@var layer: the layer the unit is present on.
	"""
	def __init__(self, unit_fife_id, x, y, layer):
		self.unit_fife_id = unit_fife_id
		self.x = x
		self.y = y
		self.layer = layer

	def __call__(self, issuer):
		"""__call__() gets called by the manager.
		@var issuer: the issuer of the command
		"""
		loc = fife.Location(game.main.game.view.layers[self.layer])
		loc.setMapCoordinates(fife.ExactModelCoordinate(self.x,self.y,0))
		game.main.game.instance_to_unit[self.unit_fife_id].move(loc)
