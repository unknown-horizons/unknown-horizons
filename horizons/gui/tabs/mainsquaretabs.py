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

from horizons.gui.widgets.productionoverview import ProductionOverview
from horizons.gui.tabs import OverviewTab
from horizons.gui.tabs.residentialtabs import setup_tax_slider

from horizons.util import Callback
from horizons.messaging import UpgradePermissionsChanged
from horizons.command.uioptions import SetSettlementUpgradePermissions
from horizons.constants import BUILDINGS, TIER
from horizons.component.tradepostcomponent import TradePostComponent
from horizons.component.namedcomponent import NamedComponent

class MainSquareTab(OverviewTab):
	"""Tab for main square. Refreshes when one building on the settlement changes"""
	def __init__(self, instance, widget, icon_path):
		super(MainSquareTab, self).__init__(instance=instance, widget=widget, icon_path=icon_path)
		self.init_values()

	@property
	def settlement(self):
		return self.instance.settlement

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

class AccountTab(MainSquareTab):
	"""Display basic income and expenses of a settlement"""
	def __init__(self, instance):
		super(AccountTab, self).__init__(instance=instance, widget='tab_account.xml', \
		                                 icon_path='content/gui/icons/tabwidget/warehouse/account_%s.png')
		self.helptext = _("Account")

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
		buy_expenses = self.settlement.get_component(TradePostComponent).buy_expenses
		sell_income = self.settlement.get_component(TradePostComponent).sell_income
		balance = self.settlement.balance
		sign = '+' if balance >= 0 else '-'
		self.widget.child_finder('taxes').text = unicode(taxes)
		self.widget.child_finder('running_costs').text = unicode(running_costs)
		self.widget.child_finder('buying').text = unicode(buy_expenses)
		self.widget.child_finder('sale').text = unicode(sell_income)
		self.widget.child_finder('balance').text = unicode(sign+' '+str(abs(balance)))

class MainSquareOverviewTab(AccountTab):
	def __init__(self, instance):
		super(MainSquareOverviewTab, self).__init__(instance=instance)
		self.helptext = _('Main square overview')
		self.widget.child_finder('headline').text = self.settlement.get_component(NamedComponent).name
		self.widget.child_finder('headline').helptext = _('Click to change the name of your settlement')

	def refresh(self):
		self.widget.child_finder('headline').text = self.settlement.get_component(NamedComponent).name
		events = {
				'headline': Callback(self.instance.session.ingame_gui.show_change_name_dialog, self.settlement)
		         }
		self.widget.mapEvents(events)
		super(MainSquareOverviewTab, self).refresh()

class MainSquareSettlerLevelTab(MainSquareTab):
	LEVEL = None # overwrite in subclass
	def __init__(self, instance, widget):
		icon_path = 'content/gui/icons/tabwidget/mainsquare/inhabitants{incr}_%s.png'.format(incr=self.__class__.LEVEL)
		super(MainSquareSettlerLevelTab, self).__init__(widget=widget, instance=instance, icon_path=icon_path)
		self.max_inhabitants = instance.session.db.get_settler_inhabitants_max(self.__class__.LEVEL)
		self.helptext = instance.session.db.get_settler_name(self.__class__.LEVEL)

		slider = self.widget.child_finder('tax_slider')
		val_label = self.widget.child_finder('tax_val_label')
		setup_tax_slider(slider, val_label, self.settlement, self.__class__.LEVEL)
		self.widget.child_finder('tax_val_label').text = unicode(self.settlement.tax_settings[self.__class__.LEVEL])

	@classmethod
	def shown_for(cls, instance):
		return instance.owner.settler_level >= cls.LEVEL

	def show(self):
		super(MainSquareSettlerLevelTab, self).show()
		UpgradePermissionsChanged.subscribe(self.refresh_via_message, sender=self.settlement)

	def hide(self):
		super(MainSquareSettlerLevelTab, self).hide()
		UpgradePermissionsChanged.unsubscribe(self.refresh_via_message, sender=self.settlement)

	def _get_last_tax_paid(self):
		houses = self.settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]
		return sum([building.last_tax_payed for building in houses if building.level == self.__class__.LEVEL])

	def _get_resident_counts(self):
		result = {}
		for building in self.settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]:
			if building.level == self.__class__.LEVEL:
				if building.inhabitants not in result:
					result[building.inhabitants] = 0
				result[building.inhabitants] += 1
		return result

	def refresh_via_message(self, message):
		# message bus requires parameter, refresh() doesn't allow parameter
		# TODO: find general solution
		self.refresh()

	def refresh(self):
		self.widget.mapEvents({
			'allow_upgrades/mouseClicked' : self.toggle_upgrades,
		})

		# refresh taxes
		self.widget.child_finder('taxes').text = unicode(self._get_last_tax_paid())

		# refresh upgrade permissions
		upgrades_button = self.widget.child_finder('allow_upgrades')
		if self.__class__.LEVEL < TIER.CURRENT_MAX: #max incr => cannot allow upgrades
			if self.settlement.upgrade_permissions[self.__class__.LEVEL]:
				upgrades_button.set_active()
				upgrades_button.helptext = _('Don\'t allow upgrades')
			else:
				upgrades_button.set_inactive()
				upgrades_button.helptext = _('Allow upgrades')

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

class MainSquareSailorsTab(MainSquareSettlerLevelTab):
	LEVEL = TIER.SAILORS
	def __init__(self, instance):
		super(MainSquareSailorsTab, self).__init__(instance, 'mainsquare_sailors.xml')

class MainSquarePioneersTab(MainSquareSettlerLevelTab):
	LEVEL = TIER.PIONEERS
	def __init__(self, instance):
		super(MainSquarePioneersTab, self).__init__(instance, 'mainsquare_pioneers.xml')

class MainSquareSettlersTab(MainSquareSettlerLevelTab):
	LEVEL = TIER.SETTLERS
	def __init__(self, instance):
		super(MainSquareSettlersTab, self).__init__(instance, 'mainsquare_settlers.xml')

class MainSquareCitizensTab(MainSquareSettlerLevelTab):
	LEVEL = TIER.CITIZENS
	def __init__(self, instance):
		super(MainSquareCitizensTab, self).__init__(instance, 'mainsquare_citizens.xml')
