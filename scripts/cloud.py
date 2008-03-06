from agent import Agent
import settings as TDS
import fife
import random

_STATE_NONE, _STATE_FLOATING, _STATE_DISAPPEAR, _STATE_APPEAR = 0, 1, 2, 3

class Cloud(Agent):
	def __init__(self, model, agentName, layer, uniqInMap=False):
		super(Cloud, self).__init__(model, agentName, layer, uniqInMap)
		self.state = _STATE_NONE
		
	def isOutOfBounds(self, c):
		return (c.x < 0) or (c.x > 100) or (c.y < 0) or (c.y > 100)

	def OnActionFinished(self, instance, action):
		if self.state == _STATE_APPEAR:
			self.move()
		elif self.state == _STATE_FLOATING:
			c = self.agent.getLocationRef().getExactLayerCoordinatesRef()
			c.x += self.x_dir
			c.y += self.y_dir
			if self.isOutOfBounds(c):
				self.disappear()
			else:
				self.move()
		elif self.state == _STATE_DISAPPEAR:
			self.agent.getLocationRef().setExactLayerCoordinates(self.initialCoords)
			self.appear()

	def start(self, x_dir, y_dir):
		self.x_dir = x_dir
		self.y_dir = y_dir
		self.loc = self.agent.getLocation()
		self.initialCoords = self.agent.getLocation().getExactLayerCoordinates()
		self.appear()
	
	def appear(self):
		self.state = _STATE_APPEAR
		self.agent.act('appear', self.loc, False)
	
	def disappear(self):
		self.state = _STATE_DISAPPEAR
		self.agent.act('disappear', self.loc, False)
	
	def move(self):
		self.state = _STATE_FLOATING
		self.agent.act('default', self.loc, False)
	