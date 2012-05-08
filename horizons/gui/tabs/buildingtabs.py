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

from horizons.constants import GAME_SPEED
from horizons.gui.tabs import OverviewTab
from horizons.util import ActionSetLoader, Callback
from horizons.scheduler import Scheduler
from horizons.component.namedcomponent import NamedComponent
from horizons.component.storagecomponent import StorageComponent


class WarehouseOverviewTab(OverviewTab):
	""" the main tab of warehouses and storages """
	def __init__(self, instance):
		super(WarehouseOverviewTab, self).__init__(
			widget = 'overview_warehouse.xml',
			instance = instance
		)
		self.widget.findChild(name="headline").text = self.instance.settlement.get_component(NamedComponent).name
		self.helptext = _("Warehouse overview")
		self._refresh_collector_utilisation()

	def _refresh_collector_utilisation(self):
		utilisation = int(round(self.instance.get_collector_utilisation() * 100))
		self.widget.findChild(name="collector_utilisation").text = unicode(utilisation) + u'%'

	def refresh(self):
		self.widget.findChild(name="headline").text = self.instance.settlement.get_component(NamedComponent).name
		events = {
				'headline': Callback(self.instance.session.ingame_gui.show_change_name_dialog, self.instance.settlement)
		         }
		self.widget.mapEvents(events)
		self._refresh_collector_utilisation()
		super(WarehouseOverviewTab, self).refresh()

	def show(self):
		super(WarehouseOverviewTab, self).show()
		Scheduler().add_new_object(Callback(self._refresh_collector_utilisation), self, run_in = GAME_SPEED.TICKS_PER_SECOND, loops = -1)

	def hide(self):
		super(WarehouseOverviewTab, self).hide()
		Scheduler().rem_all_classinst_calls(self)

	def on_instance_removed(self):
		Scheduler().rem_all_classinst_calls(self)
		super(WarehouseOverviewTab, self).on_instance_removed()

class TowerOverviewTab(OverviewTab): # defensive tower
	def __init__(self, instance):
		super(TowerOverviewTab, self).__init__(
			widget='overview_tower.xml',
			instance=instance)
		self.widget.findChild(name="headline").text = self.instance.settlement.get_component(NamedComponent).name
		self.helptext = _("Tower overview")

class SignalFireOverviewTab(OverviewTab):
	def __init__(self, instance):
		super(SignalFireOverviewTab, self).__init__(
			widget='overview_signalfire.xml',
			instance=instance)
		action_set = ActionSetLoader.get_sets()[self.instance._action_set_id]
		action_gfx = action_set.items()[0][1]
		image = action_gfx[45].keys()[0]
		self.widget.findChild(name="building_image").image = image
		self.helptext = _("Overview")

class ResourceDepositOverviewTab(OverviewTab):
	def  __init__(self, instance):
		super(ResourceDepositOverviewTab, self).__init__(
			widget='overview_resourcedeposit.xml',
			instance=instance)
		res = self.instance.session.db.get_resource_deposit_resources(self.instance.id)
		# type: [ (res, min_amount, max_amount)]
		# let it display starting from 0, not min_amount, else it looks like there's nothing in it
		# when parts of the ore have been mined already
		res_range = 0, res[0][2]
		self.widget.child_finder("inventory").init(self.instance.session.db, \
		                                           self.instance.get_component(StorageComponent).inventory,
		                                           ordinal=res_range)
	def refresh(self):
		super(ResourceDepositOverviewTab, self).refresh()
		self.widget.child_finder("inventory").update()
