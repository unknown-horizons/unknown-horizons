__all__ = ['common','object','ship']

from game.world.units import *
import game.main
import fife

class UnitClass(type):
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
		self._object.setPather(game.main.game.view.model.getPather('RoutePather'))
		self._object.setBlocking(False)
		self._object.setStatic(False)
		action = self._object.createAction('default')
		fife.ActionVisual.create(action)

		for rotation, animation_id in game.main.db.query("SELECT rotation, animation FROM data.action where unit=?", (self.id,)).rows:
			anim_id = game.main.fife.animationpool.addResourceFromFile(str(animation_id))
			action.get2dGfxVisual().addAnimation(int(rotation), anim_id)
			action.setDuration(game.main.fife.animationpool.getAnimation(anim_id).getDuration())
