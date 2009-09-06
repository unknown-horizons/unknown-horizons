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


from building import BasicBuilding, SelectableBuilding
from buildable import BuildableSingleOnCoast
from horizons.util import Point
from horizons.gui.tabs import ProductionOverviewTab, InventoryTab, BoatbuilderTab, TabWidget
from horizons.constants import UNITS
from horizons.world.production.producer import UnitProducerBuilding
from collectingbuilding import CollectingBuilding

import horizons.main

class BoatBuilder(SelectableBuilding, UnitProducerBuilding, CollectingBuilding, BuildableSingleOnCoast, BasicBuilding):
	tabs = ProductionOverviewTab, BoatbuilderTab

	def __init__(self, **kwargs):
		super(BoatBuilder, self).__init__(**kwargs)
		self.inventory.limit = 10
