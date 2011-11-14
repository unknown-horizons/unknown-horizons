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
from horizons.gui.widgets.productionoverview import ProductionOverview
from horizons.gui.tabs.overviewtab import _setup_tax_slider

from horizons.extscheduler import ExtScheduler
from horizons.util.gui import create_resource_icon
from horizons.command.uioptions import SetTaxSetting, SetSettlementUpgradePermissions
from horizons.constants import BUILDINGS, SETTLER

class MainSquareTab(TabInterface):
	"""Tab for main square. Refreshes when one building on the settlement changes"""
	def __init__(self, *args, **kwargs):
		super(MainSquareTab, self).__init__(*args, **kwargs)
		self._refresh_scheduled = False

	def show(self):
		super(MainSquareTab, self).show()
		# update self when a building of the settlement changes.
		for building in self.settlement.buildings:
			if not building.has_change_listener(self._schedule_refresh):
				building.add_change_listener(self._schedule_refresh)

	def hide(self):
		super(MainSquareTab, self).hide()
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
		super(MainSquareTab, self).refresh()
		self._refresh_scheduled = False


class AccountTab(MainSquareTab):
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

		self.widget.mapEvents({
		  'show_production_overview/mouseClicked' : self.show_production_overview
		  })

	def show_production_overview(self):
		self.prod_overview = ProductionOverview(self.settlement)
		self.prod_overview.toggle_visibility()

	def refresh(self):
		super(AccountTab, self).refresh()
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

class MainSquareSettlerTabSettlerTab(MainSquareTab):
	"""Displays information about the settlers on average as overview"""
	def __init__(self, instance):
		super(MainSquareSettlerTabSettlerTab, self).__init__(widget = 'mainsquare_inhabitants.xml')
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

class MainSquareSettlerLevelTab(MainSquareTab):
	LEVEL = None # overwrite in subclass
	def __init__(self, instance, widget):
		super(MainSquareSettlerLevelTab, self).__init__(widget = widget)
		self.settlement = instance.settlement
		self.init_values()
		icon_path = 'content/gui/icons/tabwidget/mainsquare/inhabitants%s' % self.__class__.LEVEL + '_%s.png'
		self.button_up_image = icon_path % 'u'
		self.button_active_image = icon_path % 'a'
		self.button_down_image = icon_path % 'd'
		self.button_hover_image = icon_path % 'h'

		self.max_inhabitants = instance.session.db.get_settler_inhabitants_max(self.__class__.LEVEL)

		slider = self.widget.child_finder('tax_slider')
		val_label = self.widget.child_finder('tax_val_label')
		_setup_tax_slider(slider, val_label, self.settlement, self.__class__.LEVEL)
		self.widget.child_finder('tax_val_label').text = unicode(self.settlement.tax_settings[self.__class__.LEVEL])

	@classmethod
	def shown_for(cls, instance):
		return instance.owner.settler_level >= cls.LEVEL

	def _get_last_tax_paid(self):
		return sum([building.last_tax_payed for building in self.settlement.get_buildings_by_id(BUILDINGS.RESIDENTIAL_CLASS) if \
			building.level == self.__class__.LEVEL])

	def _get_resident_counts(self):
		result = {}
		for building in self.settlement.get_buildings_by_id(BUILDINGS.RESIDENTIAL_CLASS):
			if building.level == self.__class__.LEVEL:
				if building.inhabitants not in result:
					result[building.inhabitants] = 0
				result[building.inhabitants] += 1
		return result

	def refresh(self):
		self.widget.mapEvents({
			'allow_upgrades/mouseClicked' : self.toggle_upgrades,
		})

		# refresh taxes
		self.widget.child_finder('taxes').text = unicode(self._get_last_tax_paid())

		# refresh upgrade permissions
		upgrades_button = self.widget.child_finder('allow_upgrades')
		if self.__class__.LEVEL < SETTLER.CURRENT_MAX_INCR: #max incr => cannot allow upgrades
			if self.settlement.upgrade_permissions[self.__class__.LEVEL]:
				upgrades_button.set_active()
				upgrades_button.tooltip = _('Don\'t allow upgrades')
			else:
				upgrades_button.set_inactive()
				upgrades_button.tooltip = _('Allow upgrades')

		# refresh residents per house info
		resident_counts = self._get_resident_counts()
		houses = 0
		residents = 0
		for number in xrange(1, self.max_inhabitants + 1):
			house_count = resident_counts[number] if number in resident_counts else 0
			self.widget.child_finder('resident_count_%d' % number).text = unicode(house_count)
			houses += house_count
			residents += house_count * number

		# refresh the summary
		self.widget.child_finder('house_count').text = unicode(houses)
		self.widget.child_finder('resident_count').text = unicode(residents)

		self.widget.adaptLayout()
		super(MainSquareSettlerLevelTab, self).refresh()

	def toggle_upgrades(self):
		SetSettlementUpgradePermissions(self.settlement, self.__class__.LEVEL, not self.settlement.upgrade_permissions[self.__class__.LEVEL]).execute(self.settlement.session)
		self.refresh()

class MainSquareSailorsTab(MainSquareSettlerLevelTab):
	LEVEL = SETTLER.SAILOR_LEVEL
	def __init__(self, instance):
		super(MainSquareSailorsTab, self).__init__(instance, 'mainsquare_sailors.xml')
		self.tooltip = _("Sailors")

class MainSquarePioneersTab(MainSquareSettlerLevelTab):
	LEVEL = SETTLER.PIONEER_LEVEL
	def __init__(self, instance):
		super(MainSquarePioneersTab, self).__init__(instance, 'mainsquare_pioneers.xml')
		self.tooltip = _("Pioneers")

class MainSquareSettlersTab(MainSquareSettlerLevelTab):
	LEVEL = SETTLER.SETTLER_LEVEL
	def __init__(self, instance):
		super(MainSquareSettlersTab, self).__init__(instance, 'mainsquare_settlers.xml')
		self.tooltip = _("Settlers")
