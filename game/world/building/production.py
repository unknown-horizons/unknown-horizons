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

from building import Building, Selectable
from game.world.production import SecondaryProducer
from buildable import BuildableSingleWithSurrounding
from game.gui.tabwidget import TabWidget
import game.main

class AnimalFarm(Selectable, SecondaryProducer, BuildableSingleWithSurrounding, Building):
	_surroundingBuildingClass = 18
	""" This class builds pasturage in the radius automatically,
	so that farm animals can graze there """

	def create_carriage(self):
		self.animals = []
		animals = game.main.db("SELECT animal, count from data.animals where building = ?", self.id)
		for (animal,number) in animals:
			for i in xrange(0,number):
				self.animals.append(game.main.session.entities.units[animal](self))

		self._Consumer__local_carriages.append(game.main.session.entities.units[7](self))

class Lumberjack(Selectable, SecondaryProducer, BuildableSingleWithSurrounding, Building):
	_surroundingBuildingClass = 17
	"""Class representing a Lumberjack."""
