import game.main
import fife

class SubGround(object):
	def __init__(self, x, y):
		if self._object == None:
			self.__class__._loadObject()
		self.x = x
		self.y = y
		self._instance = game.main.game.view.layers[0].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), str(self.id) + '#' + str(self._count))
		self.__class__._count += 1
		fife.InstanceVisual.create(self._instance)

class Ground(type):
	def __new__(self, id):
		return type.__new__(self, 'Ground[' + str(id) + ']', (SubGround,), {})

	def __init__(self, id):
		self.id = id
		self._object = None

	def _loadObject(self):
		print 'Loading ground #' + str(self.id) + '...'
		self._object = game.main.game.view.model.createObject(str(self.id), 'ground')
		fife.ObjectVisual.create(self._object)
		visual = self._object.get2dGfxVisual()
		self._count = 0

		for rotation, file in game.main.db.query("SELECT rotation, (select file from data.animation where data.animation.animation_id = data.action.animation order by frame_end limit 1) FROM data.action where ground=?", (self.id,)).rows:
			img = game.main.fife.imagepool.addResourceFromFile(str(file))
			visual.addStaticImage(int(rotation), img)
			img = game.main.fife.imagepool.getImage(img)
			img.setXShift(0)
			img.setYShift(0)
