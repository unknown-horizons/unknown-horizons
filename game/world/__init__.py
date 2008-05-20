__all__ = ['island', 'player', 'setlement']

class World:
	def __init__(self, **args):
		self.args = args

		self.players = []
		self.islands = []
		self.ships = []
