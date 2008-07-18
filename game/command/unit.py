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

import fife
import game.main
from game.util import Point

class Act(object):
	"""Command class that moves a unit.
	@param unit_fife_id: int FifeId of the unit that is to be moved.
	@param x,y: float coordinates where the unit is to be moved.
	@param layer: the layer the unit is present on.
	"""
	def __init__(self, unit, x, y):
		self.unit = unit._instance.getId()
		self.x = x
		self.y = y

	def __call__(self, issuer):
		"""__call__() gets called by the manager.
		@param issuer: the issuer of the command
		"""
		game.main.session.entities.getInstance(self.unit).act(self.x, self.y)
