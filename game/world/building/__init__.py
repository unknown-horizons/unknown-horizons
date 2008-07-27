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
	@param id: int - building id in the database."""
	def __new__(self, id):
		class_package, class_name = game.main.db("SELECT class_package, class_type FROM data.building WHERE rowid = ?", id)[0]
		__import__('game.world.building.'+class_package)
		return type.__new__(self, 'Building[' + str(id) + ']', (getattr(globals()[class_package], class_name),), {})

	def __init__(self, id, **kwargs):
		"""
		@param id: building id.
		"""
		super(BuildingClass, self).__init__(**kwargs)
		self.id = id
		self._object = None
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

	def _loadObject(cls):
		"""Loads building from the db.
		"""
		print 'Loading building #' + str(cls.id) + '...'
		cls._object = game.main.session.view.model.createObject(str(cls.id), 'building')
		for (action_id,) in game.main.db("SELECT action FROM data.action where building=? group by action", cls.id):
			action = cls._object.createAction(action_id)
			fife.ActionVisual.create(action)
			for rotation, animation_id in game.main.db("SELECT rotation, animation FROM data.action where building=? and action=?", cls.id, action_id):
				if rotation == 45:
					command = 'left-16,bottom+' + str(cls.size[0] * 8)
				elif rotation == 135:
					command = 'left-' + str(cls.size[1] * 16) + ',bottom+8'
				elif rotation == 225:
					command = 'left-' + str((cls.size[0] + cls.size[1] - 1) * 16) + ',bottom+' + str(cls.size[1] * 8)
				elif rotation == 315:
					command = 'left-' + str(cls.size[0] * 16) + ',bottom+' + str((cls.size[0] + cls.size[1] - 1) * 8)
				else:
					command = 'left-16,bottom+8'
				anim_id = game.main.fife.animationpool.addResourceFromFile(animation_id + ':shift:' + command)
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
