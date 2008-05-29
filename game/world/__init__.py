__all__ = ['island', 'player', 'settlement']

import game.main
from game.world.island import Island

class World(object):
	def __init__(self):
		#load properties
		self.properties = {}
		for (name, value) in game.main.db("select name, value from map.properties"):
			self.properties[name] = value

		#load islands
		self.islands = []
		for (island, offset_x, offset_y) in game.main.db("select island, x, y from map.islands"):
			self.islands.append(Island(offset_x, offset_y, island))

		#calculate map dimensions
		self.min_x, self.min_y, self.max_x, self.max_y = None, None, None, None
		for i in self.islands:
			self.min_x = i.x if self.min_x == None or i.x < self.min_x else self.min_x
			self.min_y = i.y if self.min_y == None or i.y < self.min_y else self.min_y
			self.max_x = (i.x + i.width - 1) if self.max_x == None or (i.x + i.width - 1) > self.max_x else self.max_x
			self.max_y = (i.y + i.height - 1) if self.max_y == None or (i.y + i.width - 1) > self.max_y else self.max_y
		self.min_x -= 10
		self.min_y -= 10
		self.max_x += 10
		self.max_y += 10

		#add water
		print "Filling world with water..."
		self.grounds = []
		for x in xrange(self.min_x, self.max_x):
			for y in xrange(self.min_y, self.max_y):
				for i in self.islands:
					for g in i.grounds:
						if g.x == x and g.y == y:
							break
					else: #found no instance at x,y in the island
						continue
					break
				else: #found no instance at x,y at any island
					self.grounds.append(game.main.game.entities.grounds[int(self.properties.get('default_ground', 13))](x, y))
		print "done."

		#setup players
		self.player = None
		self.players = {0:self.player}

		#add ship
		self.ships = []
		self.ships.append(game.main.game.entities.units[1](25, 25))
		self.ships.append(game.main.game.entities.units[1](29, 25))

		self.buildings = []
