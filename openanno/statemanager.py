from openanno.gamestate import GameState

class StateManager(object):
	currentState = None
	engine = None
	
	MAPFILE = 'content/datasets/maps/openanno-test-map.xml'
	
	def init(fifengine):
		engine = fifengine
		currentState = GameState(engine)
		
		w.create_world(MAPFILE)
		w.adjust_views()
	
	def run():
		currentState.run()