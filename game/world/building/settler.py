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
from game.world.consumer import Consumer
from game.gui.tabwidget import TabWidget
import game.main
from buildable import BuildableSingle
from game.util import WeakList

class Settler(Consumer, BuildableSingle, Selectable, Building):
	"""Represents a settlers house, that uses resources and creates inhabitants."""
	def __init__(self, x, y, owner, instance = None, level=1, **kwargs):
		self.level = level
		super(Settler, self).__init__(x=x, y=y, owner=owner, instance=instance, level=level, **kwargs)
		self.max_inhabitants = game.main.db("SELECT max_inhabitants FROM settler_level WHERE level=?", level)[0][0]
		print "Settler debug, max_inhabitants:", self.max_inhabitants
		self.tax_income = game.main.db("SELECT tax_income FROM settler_level WHERE level=?", level)[0][0]
		print "Settler debug, tax_income:", self.tax_income


	def _init(self):
		"""Part of initiation that __init__() and load() share"""
		self._Consumer__resources = {0: []} #ugly work arround to work with current consumer implementation
		self.local_carriages = []

		from game.world.building.building import Building
		if isinstance(self, Building):
			self.radius_coords = self.position.get_radius_coordinates(self.radius)

		self._Consumer__collectors = WeakList()
		for (res,) in game.main.db("SELECT res_id FROM settler_consumation WHERE level = ?", self.level):
			print "Settler debug, res:", res
			self._Consumer__resources[0].append(res)
			if not self.inventory.hasSlot(res):
				self.inventory.addSlot(res, 1) # TODO: fix size somewhere else!

		#create a carriage to collect the needed ressources
		print self.local_carriages
		self.create_carriage()

	def show_menu(self):
		game.main.session.ingame_gui.show_menu(TabWidget(2, self))

	def get_consumed_res(self):
		"""Returns list of resources, that the building uses, without
		considering, if it currently needs them
		"""
		return self._Consumer__resources[0]
	# TODO: saving and loading