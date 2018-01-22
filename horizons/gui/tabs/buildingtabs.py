# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from horizons.component.depositcomponent import DepositComponent
from horizons.component.namedcomponent import NamedComponent
from horizons.component.storagecomponent import StorageComponent
from horizons.i18n import gettext_lazy as LazyT
from horizons.util.loaders.actionsetloader import ActionSetLoader

from .overviewtab import OverviewTab


class TowerOverviewTab(OverviewTab): # defensive tower
	widget = 'overview_tower.xml'
	helptext = LazyT("Tower overview")

	def init_widget(self):
		super().init_widget()
		self.widget.findChild(name="headline").text = self.instance.settlement.get_component(NamedComponent).name


class SignalFireOverviewTab(OverviewTab):
	widget = 'overview_signalfire.xml'
	helptext = LazyT("Overview")

	def init_widget(self):
		super().init_widget()
		action_set = ActionSetLoader.get_set(self.instance._action_set_id)
		action_gfx = list(action_set.items())[0][1]
		image = list(action_gfx[45].keys())[0]
		self.widget.findChild(name="building_image").image = image


class ResourceDepositOverviewTab(OverviewTab):
	widget = 'overview_resourcedeposit.xml'

	def init_widget(self):
		super().init_widget()
		# display range starts 0, not min_amount, else it looks like there's nothing in it
		# when parts of the ore have been mined already
		resources = self.instance.get_component(DepositComponent).get_res_ranges()
		amounts = {res: (0, max_amount) for res, min_, max_amount in resources}
		self.widget.child_finder("inventory").init(self.instance.session.db,
		                                           self.instance.get_component(StorageComponent).inventory,
		                                           ordinal=amounts)

	def refresh(self):
		super().refresh()
		self.widget.child_finder("inventory").update()
