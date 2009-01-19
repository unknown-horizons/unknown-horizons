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

__all__ = ['building', 'housing', 'nature', 'path', 'production', 'storages', 'settler']

import game.main
import fife

class BuildingClass(type):
	"""Class that is used to create Building-Classes from the database.
	@param id: int - building id in the database.

	Note this creates classes, not instances. These are classes are created at the beginning of a session
	and are later used to create instances, when buildings are built.
	The __new__() function uses quite some python magic to construct the new class. Basically this is just cool
	and doesn't have a real benefit quite yet except for saving a litte loading time.

	TUTORIAL:
	Check out the __new__() function if you feel your pretty good with python and are interested in how it all works,
	otherwise, continue to the __init__() function.
	"""
	def __new__(self, id):
		class_package, class_name = game.main.db("SELECT class_package, class_type FROM data.building WHERE rowid = ?", id)[0]
		__import__('game.world.building.'+class_package)


		@classmethod
		def load(cls, db, worldid):
			self = cls.__new__(cls)
			super(cls, self).load(db, worldid)
			return self
		# Return the new type for this building, including it's attributes, like the previously defined load function.
		return type.__new__(self, 'Building[' + str(id) + ']',
			(getattr(globals()[class_package], class_name),),
			{"load": load})

	def __init__(self, id, **kwargs):
		"""
		Final loading for the building.
		@param id: building id.
		"""
		super(BuildingClass, self).__init__(self, **kwargs)
		self.id = id
		self._object = None
		self.class_package = game.main.db("SELECT class_package FROM data.building WHERE rowid = ?", id)[0][0]
		(size_x,  size_y) = game.main.db("SELECT size_x, size_y FROM data.building WHERE rowid = ?", id)[0]
		self.name = game.main.db("SELECT name FROM data.building WHERE rowid = ?", id)[0][0]
		self.size = (int(size_x), int(size_y))
		self.radius = game.main.db("SELECT radius FROM data.building WHERE rowid = ?", id)[0][0]
		self.health = int(game.main.db("SELECT health FROM data.building WHERE rowid = ?", id)[0][0])
		self.inhabitants = int(game.main.db("SELECT inhabitants_start FROM data.building WHERE rowid = ?", id)[0][0])
		self.inhabitants_max = int(game.main.db("SELECT inhabitants_max FROM data.building WHERE rowid = ?", id)[0][0])
		for (name,  value) in game.main.db("SELECT name, value FROM data.building_property WHERE building = ?", str(id)):
			setattr(self, name, value)
		self.costs = {}
		for (name, value) in game.main.db("SELECT resource, amount FROM data.building_costs WHERE building = ?", str(id)):
			self.costs[name]=value
		self._loadObject()
		running_costs = game.main.db("SELECT cost_active, cost_inactive FROM data.building_running_costs WHERE building=?", self.id)
		if len(running_costs) > 0:
			self.running_costs = running_costs[0][0]
			self.running_costs_inactive = running_costs[0][1]
		else:
			self.running_costs = 0
			self.running_costs_inactive = 0
		"""TUTORIAL: Now you know the basic attributes each building has. To check out further functions of single
		             buildings you should check out the seperate classes in game/world/buildings/*.
					 Unit creation is very simular, you could check it out though and see which attributes a unit
					 always has.
					 As most of the buildings are derived from the production/provider/consumer classes, which are
					 derived from the storageholder, i suggest you start digging deaper there.
					 game/world/storageholder.py is the next place to go.
					 """

	def load(cls, db, worldid):
		self = cls.__new__(cls)
		self.load(db, worlid)
		return self

	def _loadObject(cls):
		"""Loads building from the db.
		"""
		print 'Loading building #' + str(cls.id) + '...'
		try:
			cls._object = game.main.session.view.model.createObject(str(cls.id), 'building')
		except RuntimeError:
			print 'already loaded...'
			cls._object = game.main.session.view.model.getObject(str(cls.id), 'building')
			return
		action_sets = game.main.db("SELECT action_set_id FROM data.action_set WHERE building_id=?",cls.id)
		for (action_set_id,) in action_sets:
			for (action_id,) in game.main.db("SELECT action FROM data.action WHERE action_set_id=? group by action", action_set_id):
				action = cls._object.createAction(action_id+"_"+str(action_set_id))
				fife.ActionVisual.create(action)
				for rotation, animation_id in game.main.db("SELECT rotation, animation_id FROM data.action WHERE action_set_id=? and action=?", action_set_id, action_id):
					if rotation == 45:
						command = 'left-32,bottom+' + str(cls.size[0] * 16)
					elif rotation == 135:
						command = 'left-' + str(cls.size[1] * 32) + ',bottom+16'
					elif rotation == 225:
						command = 'left-' + str((cls.size[0] + cls.size[1] - 1) * 32) + ',bottom+' + str(cls.size[1] * 16)
					elif rotation == 315:
						command = 'left-' + str(cls.size[0] * 32) + ',bottom+' + str((cls.size[0] + cls.size[1] - 1) * 16)
					else:
						print "ERROR"
						continue
					anim_id = game.main.fife.animationpool.addResourceFromFile(str(animation_id) + ':shift:' + command)
					action.get2dGfxVisual().addAnimation(int(rotation), anim_id)
					action.setDuration(game.main.fife.animationpool.getAnimation(anim_id).getDuration())

		#old code, but with "correcter" image positioning
		"""for rotation, file in game.main.db("SELECT rotation, (select file from data.animation where data.animation.animation_id = data.action.animation order by frame_end limit 1) FROM data.action where object=?", cls.id):
			img = game.main.fife.imagepool.addResourceFromFile(str(file))
			visual.addStaticImage(int(rotation), img)
			img = game.main.fife.imagepool.getImage(img)
			shift_x = 1 + img.getWidth() / 2 //left
			shift_y = img.getHeight() / -2 //bottom
			#currently a bit useless
			if rotation == 45:
				shift_x = shift_x - 15
				shift_y = shift_y + cls.size[0] * 8
			elif rotation == 135:
				shift_x = shift_x - cls.size[1] * 16
				shift_y = shift_y + 8
			elif rotation == 225:
				shift_x = shift_x - (cls.size[0] + cls.size[1] - 1) * 16
				shift_y = shift_y + cls.size[1] * 8
			elif rotation == 315:
				shift_x = shift_x - cls.size[0] * 16
				shift_y = shift_y + (cls.size[0] + cls.size[1] - 1) * 8
			img.setXShift(shift_x)
			img.setYShift(shift_y)"""
