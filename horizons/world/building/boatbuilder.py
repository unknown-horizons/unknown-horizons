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


from building import BasicBuilding, Selectable
from buildable import BuildableSingle
from horizons.util import Point
from horizons.gui.tabs import ProductionOverviewTab, InventoryTab, BoatbuilderTab, TabWidget
from horizons.constants import UNITS
from horizons.world.production.unitproduction import UnitProduction

import horizons.main

class BoatBuilder(Selectable, BuildableSingle, UnitProduction, BasicBuilding):

	def __init__(self, **kwargs):
		super(BoatBuilder, self).__init__(**kwargs)
		self.inventory.limit = 10

	@classmethod
	def is_ground_build_requirement_satisfied(cls, x, y, island, **state):
		#todo: check cost line
		coast_tile_found = False
		for xx, yy in [ (xx, yy) for xx in xrange(x, x + cls.size[0]) for yy in xrange(y, y + cls.size[1]) ]:
			tile = island.get_tile(Point(xx, yy))
			classes = tile.__class__.classes
			if 'coastline' in classes:
				coast_tile_found = True
			elif 'constructible' not in classes:
				return None

		return {} if coast_tile_found else None

	def show_menu(self):
		horizons.main.session.ingame_gui.show_menu(TabWidget(tabs= [ProductionOverviewTab(self), InventoryTab(self), BoatbuilderTab(self)]))
