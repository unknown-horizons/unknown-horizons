__all__ = ['common','object','ship']

from game.world.units import *
import game.main
import fife

class Unit(type):
	def __new__(self, id):
		(class_package,  class_name) = game.main.db.query("SELECT class_package, class_type FROM data.unit WHERE rowid = ?", (id,)).rows[0]
		return type.__new__(self, 'Unit[' + str(id) + ']', (getattr(globals()[class_package], class_name),), {})

	def __init__(self, id):
		self.id = id
		self._object = None
		for (name,  value) in game.main.db.query("SELECT name, value FROM data.unit_property WHERE unit_id = ?", (str(id),)).rows:
			setattr(self, name, value)
		self._loadObject()

	def _loadObject(self):
		print 'Loading unit #' + str(self.id) + '...'
		self._object = game.main.game.view.model.createObject(str(self.id), 'unit')
		fife.ObjectVisual.create(self._object)
		visual = self._object.get2dGfxVisual()
		self._count = 0

		for rotation, file in game.main.db.query("SELECT rotation, (select file from data.animation where data.animation.animation_id = data.action.animation order by frame_end limit 1) FROM data.action where unit=?", (self.id,)).rows:
			img = game.main.fife.imagepool.addResourceFromFile(str(file))
			visual.addStaticImage(int(rotation), img)
			img = game.main.fife.imagepool.getImage(img)
			img.setXShift(0)
			img.setYShift(0)
