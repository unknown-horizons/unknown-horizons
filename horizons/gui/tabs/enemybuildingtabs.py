# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

from horizons.gui.tabs import OverviewTab
from horizons.component.namedcomponent import NamedComponent
from horizons.component.storagecomponent import StorageComponent
from horizons.component.tradepostcomponent import TradePostComponent


class EnemyBuildingOverviewTab(OverviewTab):
	def  __init__(self, instance):
		super(EnemyBuildingOverviewTab, self).__init__(
			widget = 'overview_enemybuilding.xml',
			instance = instance
		)
		self.widget.findChild(name="headline").text = self.instance.owner.name

class EnemyWarehouseOverviewTab(OverviewTab):
	def __init__(self, instance):
		super(EnemyWarehouseOverviewTab, self).__init__(
			widget = 'overview_enemywarehouse.xml',
			instance = instance
		)
		self.widget.findChild(name="headline").text = self.instance.settlement.get_component(NamedComponent).name
		self.helptext = _("Warehouse overview")

	def refresh(self):
		settlement = self.instance.settlement
		self.widget.findChild(name="headline").text = settlement.get_component(NamedComponent).name

		selling_inventory = self.widget.findChild(name='selling_inventory')
		selling_inventory.init(self.instance.session.db, settlement.get_component(StorageComponent).inventory, settlement.get_component(TradePostComponent).sell_list, True)

		buying_inventory = self.widget.findChild(name='buying_inventory')
		buying_inventory.init(self.instance.session.db, settlement.get_component(StorageComponent).inventory, settlement.get_component(TradePostComponent).buy_list, False)

		super(EnemyWarehouseOverviewTab, self).refresh()
