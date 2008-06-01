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

from game.world.building.building import *
import game.main

class Build(object):
	"""Command class that builds an object."""
	def __init__(self, building, x, y, instance = None):
		"""Create the command
		@var object_id: int objects id.
		@var x,y: int coordinates where the object is to be built.
		"""
		self.building = building.id
		self.instance = None if instance == None else instance.getId()
		self.x = int(x)
		self.y = int(y)

	def __call__(self, issuer):
		"""Execute the command
		@var issuer: the issuer of the command
		"""
		game.main.game.world.buildings.append(game.main.game.entities.buildings[self.building](self.x, self.y, issuer, game.main.game.view.layers[1].getInstance(self.instance) if self.instance != None and issuer == game.main.game.world.player else None))
		# TODO: Add building to players/settlements
