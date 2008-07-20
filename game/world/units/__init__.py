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

from game.world.units import *
import game.main
import fife

class UnitClass(type):
	def __new__(self, id):
		"""
		@param id: unit id
		"""
		(class_package,  class_name) = game.main.db("SELECT class_package, class_type FROM data.unit WHERE rowid = ?", id)[0]
		return type.__new__(self, 'Unit[' + str(id) + ']', (getattr(globals()[class_package], class_name),), {})

	def __init__(self, id):
		"""
		@param id: unit id
		"""
		self.id = id
		self._object = None
		for (name,  value) in game.main.db("SELECT name, value FROM data.unit_property WHERE unit_id = ?", str(id)):
			setattr(self, name, value)
		self._loadObject()

	def _loadObject(cls):
		"""Loads the object with all animations.
		"""
		print 'Loading unit #' + str(cls.id) + '...'
		cls._object = game.main.session.view.model.createObject(str(cls.id), 'unit')
		cls._object.setPather(game.main.session.view.model.getPather('RoutePather'))
		cls._object.setBlocking(False)
		cls._object.setStatic(False)
		for (action_id,) in game.main.db("SELECT action FROM data.action where unit=? group by action", cls.id):
			action = cls._object.createAction(str(action_id))
			fife.ActionVisual.create(action)
			for rotation, animation_id in game.main.db("SELECT rotation, animation FROM data.action where unit=? and action=?", cls.id, action_id):
				anim_id = game.main.fife.animationpool.addResourceFromFile(str(animation_id))
				action.get2dGfxVisual().addAnimation(int(rotation), anim_id)
				action.setDuration(game.main.fife.animationpool.getAnimation(anim_id).getDuration())
