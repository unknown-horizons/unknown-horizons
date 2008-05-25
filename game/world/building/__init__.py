__all__ = ['building', 'housing']

from game.world.building import *
import game.main
import fife

class BuildingClass(type):
	def __new__(self, id):
		(class_package,  class_name) = game.main.db.query("SELECT class_package, class_type FROM data.building WHERE rowid = ?", (id,)).rows[0]
		return type.__new__(self, 'Building[' + str(id) + ']', (getattr(globals()[class_package], class_name),), {})

	def __init__(self, id):
		self.id = id
		self._object = None
		(size_x,  size_y) = game.main.db.query("SELECT size_x, size_y FROM data.building WHERE rowid = ?", (id,)).rows[0]
		self.size = (int(size_x), int(size_y))
		for (name,  value) in game.main.db.query("SELECT name, value FROM data.building_property WHERE building_id = ?", (str(id),)).rows:
			setattr(self, name, value)
		self._loadObject()

	def _loadObject(self):
		print 'Loading building #' + str(self.id) + '...'
		self._object = game.main.game.view.model.createObject(str(self.id), 'building')
		fife.ObjectVisual.create(self._object)
		visual = self._object.get2dGfxVisual()

		for rotation, file in game.main.db.query("SELECT rotation, (select file from data.animation where data.animation.animation_id = data.action.animation order by frame_end limit 1) FROM data.action where object=?", (self.id,)).rows:
			img = game.main.fife.imagepool.addResourceFromFile(str(file))
			visual.addStaticImage(int(rotation), img)
			img = game.main.fife.imagepool.getImage(img)
			img.setXShift(0)
			img.setYShift(0)

	def createInstance(self, x, y):
		instance = game.main.game.view.layers[1].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), game.main.game.entities.registerInstance(self))
		fife.InstanceVisual.create(instance)
		return instance
