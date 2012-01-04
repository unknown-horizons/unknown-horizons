# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from fife import fife

import horizons.main
from horizons.util import ActionSetLoader
from horizons.world.ingametype import IngameType

class UnitClass(IngameType):

	log = logging.getLogger('world.units')

	def __new__(self, id, yaml_data=[]):
		"""
		@param id: unit id
		"""

		@classmethod
		def load(cls, session, db, worldid):
			self = cls.__new__(cls)
			self.session = session
			super(cls, self).load(db, worldid)
			return self

		attributes = {'load': load}

		self.class_package = yaml_data['classpackage']
		self.class_type = yaml_data['classtype']
		__import__('horizons.world.units.'+self.class_package)

		return type.__new__(self, 'Unit[' + str(id) + ']',
			(getattr(globals()[self.class_package], self.class_type),),
			attributes)

	def __init__(self, id, yaml_data=[]):
		"""
		@param id: unit id.
		"""
		super(UnitClass, self).__init__(self)
		self.id = id
		self._object = None
		self.action_sets = yaml_data['actionsets']
		self.action_sets_by_level = self.action_sets_by_level(self.action_sets)
		self._loadObject()
		self.classname = yaml_data['classname']
		self.radius = yaml_data['radius']
		self.component_templates = yaml_data['components']
	def _loadObject(cls):
		"""Loads the object with all animations.
		"""
		cls.log.debug('Loading unit %s', cls.id)
		try:
			cls._object = horizons.main.fife.engine.getModel().createObject(str(cls.id), 'unit')
		except RuntimeError:
			cls.log.debug('Already loaded unit %s', cls.id)
			cls._object = horizons.main.fife.engine.getModel().getObject(str(cls.id), 'unit')
			return
		cls._object.setPather(horizons.main.fife.engine.getModel().getPather('RoutePather'))
		cls._object.setBlocking(False)
		cls._object.setStatic(False)
		action_sets = ActionSetLoader.get_sets()
		for action_set_id in cls.action_sets:
			for action_id in action_sets[action_set_id].iterkeys():
				action = cls._object.createAction(action_id+"_"+str(action_set_id))
				fife.ActionVisual.create(action)
				for rotation in action_sets[action_set_id][action_id].iterkeys():
					anim = horizons.main.fife.animationloader.loadResource( \
						str(action_set_id)+"+"+str(action_id)+"+"+ \
						str(rotation) + ':shift:center+0,bottom+8')
					action.get2dGfxVisual().addAnimation(int(rotation), anim)
					action.setDuration(anim.getDuration())
