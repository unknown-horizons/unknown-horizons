# -*- coding: utf-8 -*-
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

__all__ = ['building', 'housing', 'nature', 'path', 'production', 'storages', 'settler', 'boatbuilder']

import logging

import horizons.main
import fife

from horizons.util import ActionSetLoader

class BuildingClass(type):
	"""Class that is used to create Building-Classes from the database.
	@param id: int - building id in the database.

	Note this creates classes, not instances. These are classes are created at the beginning of a session
	and are later used to create instances, when buildings are built.
	The __new__() function uses quite some python magic to construct the new class. Basically this is just cool
	and doesn't have a real benefit quite yet except for saving a little loading time.

	TUTORIAL:
	Check out the __new__() function if you feel your pretty good with python and are interested in how it all works,
	otherwise, continue to the __init__() function.
	"""
	log = logging.getLogger('world.building')

	def __new__(self, db, id):
		class_package, class_name = db("SELECT class_package, class_type FROM data.building WHERE id = ?", id)[0]
		__import__('horizons.world.building.'+class_package)


		@classmethod
		def load(cls, db, worldid):
			self = cls.__new__(cls)
			super(cls, self).load(db, worldid)
			return self
		# Return the new type for this building, including it's attributes, like the previously defined load function.
		return type.__new__(self, 'Building[%s]' % str(id),
			(getattr(globals()[class_package], class_name),),
			{'load': load})

	def __init__(self, db, id):
		"""
		Final loading for the building.
		@param id: building id.
		@param db: DbReader
		"""
		super(BuildingClass, self).__init__(self)
		self.id = id
		self.db = db
		self._object = None

		self.class_package, size_x, size_y, name, self.radius, health, inhabitants, inhabitants_max = \
		    self.db("SELECT class_package, size_x, size_y, name, radius, health, \
		    inhabitants_start, inhabitants_max FROM data.building WHERE id = ?", id)[0]
		self.name = _(name)
		self.size = (int(size_x), int(size_y))
		self.health = int(health)
		self.inhabitants = int(inhabitants)
		self.inhabitants_max = int(inhabitants_max)
		for (name,  value) in self.db("SELECT name, value FROM data.building_property WHERE building = ?", str(id)):
			setattr(self, name, value)
		self.costs = {}
		for (name, value) in self.db("SELECT resource, amount FROM data.building_costs WHERE building = ?", str(id)):
			self.costs[name]=value
		self._loadObject()
		running_costs = self.db("SELECT cost_active, cost_inactive FROM data.building_running_costs WHERE building=?", self.id)
		if len(running_costs) > 0:
			self.running_costs = running_costs[0][0]
			self.running_costs_inactive = running_costs[0][1]
		else:
			self.running_costs = 0
			self.running_costs_inactive = 0
		soundfiles = self.db("SELECT file FROM sounds INNER JOIN building_sounds ON \
			sounds.rowid = building_sounds.sound AND building_sounds.building = ?", self.id)
		self.soundfiles = [ i[0] for i in soundfiles ]
		"""TUTORIAL: Now you know the basic attributes each building has. To check out further functions of single
		             buildings you should check out the separate classes in horizons/world/buildings/*.
					 Unit creation is very similar, you could check it out though and see which attributes a unit
					 always has.
					 As most of the buildings are derived from the production/provider/consumer classes, which are
					 derived from the storageholder, i suggest you start digging deeper there.
					 horizons/world/storageholder.py is the next place to go.
					 """

	def _loadObject(cls):
		"""Loads building from the db.
		"""
		cls.log.debug("Loading building %s", cls.id)
		try:
			#cls._object = horizons.main.session.view.model.createObject(str(cls.id), 'building')
			cls._object = horizons.main.fife.engine.getModel().createObject(str(cls.id), 'building')
		except RuntimeError:
			cls.log.debug("Already loaded building %s", cls.id)
			cls._object = horizons.main.fife.engine.getModel().getObject(str(cls.id), 'building')
			return
		action_sets = cls.db("SELECT action_set_id FROM data.action_set WHERE object_id=?",cls.id)
		all_action_sets = ActionSetLoader.get_action_sets()
		for (action_set_id,) in action_sets:
			for action_id in all_action_sets[action_set_id].iterkeys():
				action = cls._object.createAction(action_id+"_"+str(action_set_id))
				fife.ActionVisual.create(action)
				for rotation in all_action_sets[action_set_id][action_id].iterkeys():
					#print "rotation:", rotation
					if rotation == 45:
						command = 'left-32,bottom+' + str(cls.size[0] * 16)
					elif rotation == 135:
						command = 'left-' + str(cls.size[1] * 32) + ',bottom+16'
					elif rotation == 225:
						command = 'left-' + str((cls.size[0] + cls.size[1] - 1) * 32) + ',bottom+' + str(cls.size[1] * 16)
					elif rotation == 315:
						command = 'left-' + str(cls.size[0] * 32) + ',bottom+' + str((cls.size[0] + cls.size[1] - 1) * 16)
					else:
						assert False, "Bad rotation for action_set %(id)s: %(rotation)s for action: %(action_id)s" % \
							   { 'id':action_set_id, 'rotation': rotation, 'action_id': action_id }
					anim_id = horizons.main.fife.animationpool.addResourceFromFile(str(action_set_id)+"-"+str(action_id)+"-"+str(rotation) + ':shift:' + command)
					action.get2dGfxVisual().addAnimation(int(rotation), anim_id)
					action.setDuration(horizons.main.fife.animationpool.getAnimation(anim_id).getDuration())
