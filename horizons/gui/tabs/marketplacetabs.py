# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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
import heapq
import operator

import horizons.main

from horizons.gui.tabs.tabinterface import TabInterface

from horizons.extscheduler import ExtScheduler
from horizons.gui.utility import create_resource_icon

class MarketPlaceTab(TabInterface):
	"""Tab for marketplace. Refreshes when one building on the settlement changes"""
	def __init__(self, *args, **kwargs):
		super(MarketPlaceTab, self).__init__(*args, **kwargs)
		self._refresh_scheduled = False

	def show(self):
		super(MarketPlaceTab, self).show()
		# update self when a building of the settlement changes.
		for building in self.settlement.buildings:
			if not building.has_change_listener(self._schedule_refresh):
				building.add_change_listener(self._schedule_refresh)

	def hide(self):
		super(MarketPlaceTab, self).hide()
		for building in self.settlement.buildings:
			if building.has_change_listener(self._schedule_refresh):
				building.remove_change_listener(self._schedule_refresh)

	def _schedule_refresh(self):
		"""Schedule a refresh soon, dropping all other refresh request, that appear until then.
		This saves a lot of CPU time, if you have a huge island, or play on high speed."""
		if not self._refresh_scheduled:
			self._refresh_scheduled = True
			ExtScheduler().add_new_object(self.refresh, self, run_in=0.3)

	def refresh(self):
		super(MarketPlaceTab, self).refresh()
		self._refresh_scheduled = False


class AccountTab(MarketPlaceTab):
	"""Display basic income and expenses of a settlement"""
	def __init__(self, instance):
		super(AccountTab, self).__init__(widget = 'tab_account.xml')
		self.settlement = instance.settlement
		self.init_values()
		icon_path = 'content/gui/icons/tabwidget/branchoffice/account_%s.png'
		self.button_up_image = icon_path % 'u'
		self.button_active_image = icon_path % 'a'
		self.button_down_image = icon_path % 'd'
		self.button_hover_image = icon_path % 'h'
		self.tooltip = _("Account")

	def refresh(self):
		taxes = self.settlement.cumulative_taxes
		running_costs = self.settlement.cumulative_running_costs
		buy_expenses = self.settlement.buy_expenses
		sell_income = self.settlement.sell_income
		balance = self.settlement.balance
		sign = '+' if balance >= 0 else '-'
		self.widget.child_finder('taxes').text = unicode(taxes)
		self.widget.child_finder('running_costs').text = unicode(running_costs)
		self.widget.child_finder('buying').text = unicode(buy_expenses)
		self.widget.child_finder('sale').text = unicode(sell_income)
		self.widget.child_finder('balance').text = unicode(sign+' '+str(abs(balance)))

class MarketPlaceSettlerTabSettlerTab(MarketPlaceTab):
	"""Displays information about the settlers on average as overview"""
	def __init__(self, instance):
		super(MarketPlaceSettlerTabSettlerTab, self).__init__(widget = 'mainsquare_inhabitants.xml')
		self.settlement = instance.settlement
		self.init_values()
		icon_path = 'content/gui/icons/widgets/cityinfo/inhabitants.png'
		self.button_up_image = icon_path
		self.button_active_image = icon_path
		self.button_down_image = icon_path
		self.button_hover_image = icon_path
		self.tooltip = _("Settler overview")

		self._old_most_needed_res_icon = None

	def refresh(self):
		happinesses = []
		needed_res = {}
		for building in self.settlement.buildings:
			if hasattr(building, 'happiness'):
				happinesses.append(building.happiness)
				for res in building.get_currently_not_consumed_resources():
					try:
						needed_res[res] += 1
					except KeyError:
						needed_res[res] = 1

		num_happinesses = max(len(happinesses), 1) # make sure not to divide by 0
		avg_happiness = int( sum(happinesses, 0.0) / num_happinesses )
		self.widget.child_finder('avg_happiness').text = unicode(avg_happiness) + u'/100'

		container = self.widget.child_finder('most_needed_res_container')
		if self._old_most_needed_res_icon is not None:
			container.removeChild(self._old_most_needed_res_icon)
			self._old_most_needed_res_icon = None

		if len(needed_res) > 0:
			most_need_res = heapq.nlargest(1, needed_res.iteritems(), operator.itemgetter(1))[0][0]
			most_needed_res_icon = create_resource_icon(most_need_res, horizons.main.db)
			container.addChild(most_needed_res_icon)
			self._old_most_needed_res_icon = most_needed_res_icon
		container.adaptLayout()
