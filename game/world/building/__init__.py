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

__all__ = ['building', 'housing']

from game.world.building import *
import game.main
import fife

class BuildingClass(type):
	def __new__(self, id):
		(class_package,  class_name) = game.main.db("SELECT class_package, class_type FROM data.building WHERE rowid = ?", id)[0]
		return type.__new__(self, 'Building[' + str(id) + ']', (getattr(globals()[class_package], class_name),), {})

	def __init__(self, id):
		self.id = id
		self._object = None
		(size_x,  size_y) = game.main.db("SELECT size_x, size_y FROM data.building WHERE rowid = ?", id)[0]
		self.size = (int(size_x), int(size_y))
		self.radius = game.main.db("SELECT radius FROM data.building WHERE rowid = ?", id)[0][0]
		for (name,  value) in game.main.db("SELECT name, value FROM data.building_property WHERE building_id = ?", str(id)):
			setattr(self, name, value)
		self.costs = {}
		for (name, value) in game.main.db("SELECT ressource_id, amount FROM data.building_costs WHERE building_id = ?", str(id)):
			self.costs[name]=value
		self._loadObject()

	def _loadObject(self):
		print 'Loading building #' + str(self.id) + '...'
		self._object = game.main.session.view.model.createObject(str(self.id), 'building')
		fife.ObjectVisual.create(self._object)
		visual = self._object.get2dGfxVisual()

		for rotation, file in game.main.db("SELECT rotation, (select file from data.animation where data.animation.animation_id = data.action.animation order by frame_end limit 1) FROM data.action where object=?", self.id):
			img = game.main.fife.imagepool.addResourceFromFile(str(file))
			visual.addStaticImage(int(rotation), img)
			img = game.main.fife.imagepool.getImage(img)
			shift_x = img.getWidth() / 2
			shift_y = img.getHeight() / -2
			#currently a bit useless
			if rotation == 45:
				shift_x = shift_x - self.size[0] * 16
				shift_y = shift_y + 8
			elif rotation == 135:
				shift_x = shift_x - (self.size[0] + self.size[1] - 1) * 16
				shift_y = shift_y + self.size[0] * 8
			elif rotation == 225:
				shift_x = shift_x - self.size[1] * 16
				shift_y = shift_y + (self.size[0] + self.size[1] - 1) * 8
			elif rotation == 315:
				shift_x = shift_x - 16
				shift_y = shift_y + self.size[0] * 8
			img.setXShift(shift_x)
			img.setYShift(shift_y)

	def createInstance(self, x, y):
		instance = game.main.session.view.layers[1].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), game.main.session.entities.registerInstance(self))
		fife.InstanceVisual.create(instance)
		return instance
