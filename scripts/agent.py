import common, fife

class Agent(fife.InstanceListener):
	def __init__(self, model, agentName, layer, uniqInMap=True):
		fife.InstanceListener.__init__(self)
		self.model = model
		self.agentName = agentName
		self.layer = layer
		if uniqInMap:
			self.agent = layer.getInstances('name', agentName)[0]
			self.agent.addListener(self)

	def OnActionFinished(self, instance, action):
		raise ProgrammingError('No OnActionFinished defined for Agent')

	def start(self):
		raise ProgrammingError('No start defined for Agent')
	

def create_anonymous_agents(model, objectName, layer, agentClass):
	agents = []
	instances = [a for a in layer.getInstances() if a.getObject().Id() == objectName]
	i = 0
	for a in instances:
		agentName = '%s:i:%d' % (objectName, i)
		i += 1
		agent = agentClass(model, agentName, layer, False)
		agent.agent = a
		a.addListener(agent)
		agents.append(agent)
	return agents