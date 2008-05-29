import game.main
import fife

class Ground(object):
	def __init__(self, x, y):
		if self._object == None:
			self.__class__._loadObject()
		self.x = x
		self.y = y
		self._instance = game.main.game.view.layers[0].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), game.main.game.entities.registerInstance(self))
		fife.InstanceVisual.create(self._instance)

class GroundClass(type):
	def __new__(self, id):
		return type.__new__(self, 'Ground[' + str(id) + ']', (Ground,), {})

	def __init__(self, id):
		self.id = id
		self._object = None

	def _loadObject(self):
		print 'Loading ground #' + str(self.id) + '...'
		self._object = game.main.game.view.model.createObject(str(self.id), 'ground')
		fife.ObjectVisual.create(self._object)
		visual = self._object.get2dGfxVisual()

		#for (oid, multi_action_or_animated) in game.main.db.query("SELECT id, max(actions_and_images) > 1 AS multi_action_or_animated FROM ( SELECT ground.oid as id, action.animation as animation, count(*) as actions_and_images FROM ground LEFT JOIN action ON action.ground = ground.oid LEFT JOIN animation ON action.animation = animation.animation_id GROUP BY ground.oid, action.rotation ) x GROUP BY id").rows:
		#	print oid, multi_action_or_animated
		for rotation, file in game.main.db("SELECT rotation, (select file from data.animation where data.animation.animation_id = data.action.animation order by frame_end limit 1) FROM data.action where ground=?", self.id):
			img = game.main.fife.imagepool.addResourceFromFile(str(file))
			visual.addStaticImage(int(rotation), img)
			img = game.main.fife.imagepool.getImage(img)
			img.setXShift(0)
			img.setYShift(0)
