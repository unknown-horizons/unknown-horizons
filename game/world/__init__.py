__all__ = ['island', 'player', 'setlement']

class World:
	def __init__(self):
		self.player = None
		self.players = {0:self.player}
		self.islands = []
		self.ships = []
