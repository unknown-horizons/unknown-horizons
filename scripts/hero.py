import random
from agent import Agent
import settings as TDS

_STATE_NONE, _STATE_IDLE, _STATE_RUN = 0, 1, 2

class Hero(Agent):
	def __init__(self, model, agentName, layer, uniqInMap=True):
		super(Hero, self).__init__(model, agentName, layer, uniqInMap)
		self.state = _STATE_NONE

	def OnActionFinished(self, instance, action):
		self.idle()

	def start(self):
		self.idle()
	
	def idle(self):
		self.state = _STATE_IDLE
		self.agent.act('idle', self.agent.getFacingLocation(), True)
		
	def run(self, location):
		self.state = _STATE_RUN
		self.agent.move('run', location, 4 * TDS.TestAgentSpeed)
		
		txtindex = random.randint(0, len(TDS.agentTexts)-1)
		self.agent.say(TDS.agentTexts[txtindex], 2500)

	