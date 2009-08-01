# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
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

__all__ = ['animal','nature','ship','unit']

import logging

import fife

import horizons.main

class UnitClass(type):
	def __new__(self, id):
		"""
		@param id: unit id
		"""
		log = logging.getLogger('world.units')

		@classmethod
		def load(cls, db, worldid):
			self = cls.__new__(cls)
			super(cls, self).load(db, worldid)
			return self

		attributes = {'load': load}
		attributes.update(horizons.main.db("SELECT name, value FROM data.unit_property WHERE unit = ?", str(id)))

		self.class_package,  self.class_name = horizons.main.db("SELECT class_package, class_type FROM data.unit WHERE id = ?", id)[0]
		__import__('horizons.world.units.'+self.class_package)

		return type.__new__(self, 'Unit[' + str(id) + ']',
			(getattr(globals()[self.class_package], self.class_name),),
			attributes)

	def __init__(self, id, **kwargs):
		"""
		@param id: building id.
		"""
		super(UnitClass, self).__init__(self, **kwargs)
		self.id = id
		self._object = None
		self._loadObject()
		self.radius = int(horizons.main.db("SELECT radius FROM data.unit WHERE id=?", id)[0][0])

	def _loadObject(cls):
		"""Loads the object with all animations.
		"""
		cls.log.debug('Loading unit %s', cls.id)
		try:
			cls._object = horizons.main.session.view.model.createObject(str(cls.id), 'unit')
		except RuntimeError:
			cls.log.debug('Already loaded unit %s', cls.id)
			cls._object = horizons.main.session.view.model.getObject(str(cls.id), 'unit')
			return
		cls._object.setPather(horizons.main.session.view.model.getPather('RoutePather'))
		cls._object.setBlocking(False)
		cls._object.setStatic(False)
		for (action_set_id,) in horizons.main.db("SELECT action_set_id FROM data.action_set WHERE object_id=?",cls.id):
			for action_id in horizons.main.action_sets[action_set_id].iterkeys():
				action = cls._object.createAction(action_id+"_"+str(action_set_id))
				fife.ActionVisual.create(action)
				for rotation in horizons.main.action_sets[action_set_id][action_id].iterkeys():
					anim_id = horizons.main.fife.animationpool.addResourceFromFile( \
						str(action_set_id)+"-"+str(action_id)+"-"+ \
						str(rotation) + ':shift:center+0,bottom+8')
					action.get2dGfxVisual().addAnimation(int(rotation), anim_id)
					action.setDuration(horizons.main.fife.animationpool.getAnimation(anim_id).getDuration())
