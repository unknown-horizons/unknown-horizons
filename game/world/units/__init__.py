# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

__all__ = ['animal','collector','nature','ship','unit']

import game.main
import fife

class UnitClass(type):
	def __new__(self, id):
		"""
		@param id: unit id
		"""
		
		@classmethod
		def load(cls, db, worldid):
			self = cls.__new__(cls)
			super(cls, self).load(db, worldid)
			return self
		
		attributes = {'load': load, 'id': id, '_object': self._loadObject(id)}
		attributes.update(game.main.db("SELECT name, value FROM data.unit_property WHERE unit = ?", str(id)))
		
		class_package,  class_name = game.main.db("SELECT class_package, class_type FROM data.unit WHERE rowid = ?", id)[0]
		__import__('game.world.units.'+class_package)
		
		return type.__new__(self, 'Unit[' + str(id) + ']',
			(getattr(globals()[class_package], class_name),),
			attributes)
	
	@staticmethod
	def _loadObject(id):
		"""Loads the object with all animations.
		"""
		print 'Loading unit #' + str(id) + '...'
		try:
			_object = game.main.session.view.model.createObject(str(id), 'unit')
		except RuntimeError:
			print 'already loaded...'
			_object = game.main.session.view.model.getObject(str(id), 'unit')
			return _object
		_object.setPather(game.main.session.view.model.getPather('RoutePather'))
		_object.setBlocking(False)
		_object.setStatic(False)
		for (action_id,) in game.main.db("SELECT action FROM data.action where unit=? group by action", id):
			action = _object.createAction(action_id)
			fife.ActionVisual.create(action)
			for rotation, animation_id in game.main.db("SELECT rotation, animation FROM data.action where unit=? and action=?", id, action_id):
				anim_id = game.main.fife.animationpool.addResourceFromFile(str(animation_id) + ':shift:center+0,bottom+8')
				action.get2dGfxVisual().addAnimation(int(rotation), anim_id)
				action.setDuration(game.main.fife.animationpool.getAnimation(anim_id).getDuration())
		return _object
