import fife, fifelog

class World(object):
	def __init__(self, gamestate):
		self.gamestate = gamestate
		self.players = []