from agent import Agent
import settings as TDS
import fife

_STATE_NONE, _STATE_IDLE, _STATE_RUN, _STATE_FOLLOW = 0, 1, 2, 3

GIRL_SPEED = 3 * TDS.TestAgentSpeed
class Girl(Agent):
	def __init__(self, model, agentName, layer, uniqInMap=True):
		super(Girl, self).__init__(model, agentName, layer, uniqInMap)
		self.state = _STATE_NONE
		self.waypoints = ((67, 80), (75, 44))
		self.waypoint_counter = 0
		self.hero = self.layer.getInstances('name', 'PC')[0]

	def OnActionFinished(self, instance, action):
		if self.state in (_STATE_RUN, _STATE_FOLLOW):
			self.idle()
		else:
			if self.waypoint_counter % 3:
				self.waypoint_counter += 1
				self.follow_hero()
			else:
				self.run(self.getNextWaypoint())

	def getNextWaypoint(self):
		self.waypoint_counter += 1
		l = fife.Location(self.layer)
		l.setLayerCoordinates(fife.ModelCoordinate(*self.waypoints[self.waypoint_counter % len(self.waypoints)]))
		return l
	
	def start(self):
		self.follow_hero()
	
	def idle(self):
		self.state = _STATE_IDLE
		self.agent.act('default', self.agent.getFacingLocation(), False)
		
	def follow_hero(self):
		self.state = _STATE_FOLLOW
		self.agent.follow('run', self.hero, GIRL_SPEED)
		
	def run(self, location):
		self.state = _STATE_RUN
		self.agent.move('run', location, GIRL_SPEED)
	