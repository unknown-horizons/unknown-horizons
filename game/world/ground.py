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

import game.main
import fife

class Ground(object):
	def __init__(self, x, y):
		"""
		@param x: int x position the ground is created.
		@param y: int y position the ground is created.
		"""
		if self._object == None:
			self.__class__._loadObject()
		self.x = x
		self.y = y
		self._instance = game.main.session.view.layers[0].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), game.main.session.entities.registerInstance(self))
		fife.InstanceVisual.create(self._instance)

class GroundClass(type):
	"""
	@param id: ground id.
	"""
	def __init__(self, id):
		self.id = id
		self._object = None

	def __new__(self, id):
		"""
		@param id: ground id.
		"""
		return type.__new__(self, 'Ground[' + str(id) + ']', (Ground,), {})

	def _loadObject(self):
		""" Loads the ground object from the db (animations, etc)
		"""
		print 'Loading ground #' + str(self.id) + '...'
		self._object = game.main.session.view.model.createObject(str(self.id), 'ground')
		fife.ObjectVisual.create(self._object)
		visual = self._object.get2dGfxVisual()

		#for (oid, multi_action_or_animated) in game.main.db("SELECT id, max(actions_and_images) > 1 AS multi_action_or_animated FROM ( SELECT ground.oid as id, action.animation as animation, count(*) as actions_and_images FROM ground LEFT JOIN action ON action.ground = ground.oid LEFT JOIN animation ON action.animation = animation.animation_id GROUP BY ground.oid, action.rotation ) x GROUP BY id"):
		#	print oid, multi_action_or_animated
		for rotation, file in game.main.db("SELECT rotation, (select file from data.animation where data.animation.animation_id = data.action.animation order by frame_end limit 1) FROM data.action where ground=?", self.id):
			img = game.main.fife.imagepool.addResourceFromFile(str(file))
			visual.addStaticImage(int(rotation), img)
			img = game.main.fife.imagepool.getImage(img)
			img.setXShift(0)
			img.setYShift(0)
