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

from functools import partial

from fife.extensions.pychan.widgets import Label

from horizons.command.uioptions import SetSettlementUpgradePermissions
from horizons.component.collectingcomponent import CollectingComponent
from horizons.component.namedcomponent import NamedComponent
from horizons.component.selectablecomponent import SelectableComponent
from horizons.component.tradepostcomponent import TradePostComponent
from horizons.constants import BUILDINGS, TIER
from horizons.gui.widgets.productionoverview import ProductionOverview
from horizons.i18n import gettext as T, gettext_lazy as LazyT
from horizons.messaging import PlayerLevelUpgrade, UpgradePermissionsChanged
from horizons.util.python.callback import Callback

from .overviewtab import OverviewTab
from .residentialtabs import setup_tax_slider


class MainSquareTab(OverviewTab):
	"""Tab for main square. Refreshes when one building on the settlement changes"""
	@property
	def settlement(self):
		return self.instance.settlement

	def show(self):
		super().show()
		PlayerLevelUpgrade.subscribe(self.on_player_level_upgrade)
		# update self when a building of the settlement changes.
		for building in self.settlement.buildings:
			if not building.has_change_listener(self._schedule_refresh):
				building.add_change_listener(self._schedule_refresh)

	def hide(self):
		super().hide()
		PlayerLevelUpgrade.discard(self.on_player_level_upgrade)
		for building in self.settlement.buildings:
			building.discard_change_listener(self._schedule_refresh)

	def on_player_level_upgrade(self, message):
		self.hide()
		self.instance.get_component(SelectableComponent).show_menu(jump_to_tabclass=type(self))


class AccountTab(MainSquareTab):
	"""Display basic income and expenses of a settlement"""
	widget = 'tab_account.xml'
	icon_path = 'icons/tabwidget/warehouse/account'
	helptext = LazyT("Account")

	def init_widget(self):
		super().init_widget()
		self.widget.mapEvents({
		  'show_production_overview/mouseClicked': self.show_production_overview,
		})

		# FIXME having to access the WindowManager this way is pretty ugly
		self._windows = self.instance.session.ingame_gui.windows
		self.prod_overview = ProductionOverview(self._windows, self.settlement)

		self.widget.child_finder('headline').text = self.settlement.get_component(NamedComponent).name
		self.widget.child_finder('headline').helptext = T('Click to change the name of your settlement')

		path = 'icons/widgets/cityinfo/settlement_{}'.format(self.settlement.owner.color.name)
		self.widget.child_finder('show_production_overview').path = path

	def show_production_overview(self):
		self._windows.toggle(self.prod_overview)

	def refresh(self):
		super().refresh()
		self.refresh_collector_utilization()
		taxes = self.settlement.cumulative_taxes
		running_costs = self.settlement.cumulative_running_costs
		buy_expenses = self.settlement.get_component(TradePostComponent).buy_expenses
		sell_income = self.settlement.get_component(TradePostComponent).sell_income
		balance = self.settlement.balance
		sign = '+' if balance >= 0 else '-'
		self.widget.child_finder('taxes').text = str(taxes)
		self.widget.child_finder('running_costs').text = str(running_costs)
		self.widget.child_finder('buying').text = str(buy_expenses)
		self.widget.child_finder('sale').text = str(sell_income)
		self.widget.child_finder('balance').text = str(sign + ' ' + str(abs(balance)))
		self.widget.child_finder('headline').text = self.settlement.get_component(NamedComponent).name
		rename = Callback(self.instance.session.ingame_gui.show_change_name_dialog, self.settlement)
		self.widget.mapEvents({'headline': rename})

	def refresh_collector_utilization(self):
		if self.instance.has_component(CollectingComponent):
			utilization = int(round(self.instance.get_collector_utilization() * 100))
			utilization = str(utilization) + '%'
		else:
			utilization = '---'
		self.widget.findChild(name="collector_utilization").text = utilization


class MainSquareOverviewTab(AccountTab):
	helptext = LazyT('Main square overview')

	def init_widget(self):
		super().init_widget()
		self.widget.child_finder('headline').text = self.settlement.get_component(NamedComponent).name
		self.widget.child_finder('headline').helptext = T('Click to change the name of your settlement')


class MainSquareSettlerLevelTab(MainSquareTab):
	widget = "mainsquare_inhabitants.xml"
	# overwrite in subclass
	LEVEL = None # type: int

	def __init__(self, instance):
		self.max_inhabitants = instance.session.db.get_tier_inhabitants_max(self.__class__.LEVEL)
		self.min_inhabitants = instance.session.db.get_tier_inhabitants_min(self.__class__.LEVEL)
		self.helptext = LazyT(instance.session.db.get_settler_name(self.__class__.LEVEL))

		icon_path = 'icons/tabwidget/mainsquare/inhabitants{tier}'.format(tier=self.__class__.LEVEL)
		super().__init__(instance=instance, icon_path=icon_path)

	def init_widget(self):
		super().init_widget()
		slider = self.widget.child_finder('tax_slider')
		val_label = self.widget.child_finder('tax_val_label')
		setup_tax_slider(slider, val_label, self.settlement, self.__class__.LEVEL)
		self.widget.child_finder('tax_val_label').text = str(self.settlement.tax_settings[self.__class__.LEVEL])
		self.widget.child_finder('headline').text = T(self.instance.session.db.get_settler_name(self.__class__.LEVEL))

		if self.__class__.LEVEL == TIER.CURRENT_MAX:
			# highest currently playable tier => upgrades not possible
			upgrades_label = self.widget.child_finder('upgrades_lbl')
			upgrades_label.text = T("Upgrade not possible:")
			upgrades_button = self.widget.child_finder('allow_upgrades')
			upgrades_button.set_inactive()
			upgrades_button.helptext = T("This is the highest playable tier for now!")

	@classmethod
	def shown_for(cls, instance):
		return instance.owner.settler_level >= cls.LEVEL

	def show(self):
		super().show()
		UpgradePermissionsChanged.subscribe(self.refresh_via_message, sender=self.settlement)

	def hide(self):
		super().hide()
		UpgradePermissionsChanged.discard(self.refresh_via_message, sender=self.settlement)

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
			'allow_upgrades/mouseClicked': self.toggle_upgrades,
		})

		# refresh taxes
		self.widget.child_finder('taxes').text = str(self._get_last_tax_paid())

		# refresh upgrade permissions
		upgrades_button = self.widget.child_finder('allow_upgrades')
		# The currently highest playable tier cannot allow upgrades.
		if self.__class__.LEVEL < TIER.CURRENT_MAX:
			if self.settlement.upgrade_permissions[self.__class__.LEVEL]:
				upgrades_button.set_active()
				upgrades_button.helptext = T("Don't allow upgrades")
			else:
				upgrades_button.set_inactive()
				upgrades_button.helptext = T('Allow upgrades')

		# refresh residents per house info
		resident_counts = self._get_resident_counts()
		houses = 0
		residents = 0
		container = self.widget.child_finder('residents_per_house_table')
		space_per_label = container.size[0] // 6
		for number in range(self.min_inhabitants, self.max_inhabitants + 1):
			column = number - (self.min_inhabitants - 1 if self.min_inhabitants > 0 else 0)
			house_count = resident_counts.get(number, 0)
			houses += house_count
			residents += house_count * number
			position_x = (space_per_label * (column - 1)) + 10
			if not container.findChild(name="resident_" + str(column)):
				label = Label(name="resident_" + str(column), position=(position_x, 0), text=str(number))
				container.addChild(label)
				count_label = Label(name="resident_count_" + str(column), position=(position_x - 1, 20), text=str(house_count))
				container.addChild(count_label)
			else:
				container.findChild(name="resident_" + str(column)).text = str(number)
				container.findChild(name="resident_count_" + str(column)).text = str(house_count)

		sad = self.instance.session.db.get_lower_happiness_limit()
		happy = self.instance.session.db.get_upper_happiness_limit()
		inhabitants = partial(self.settlement.get_residentials_of_lvl_for_happiness,
		                      self.__class__.LEVEL)
		self.widget.child_finder('sad_amount').text = str(inhabitants(max_happiness=sad))
		self.widget.child_finder('avg_amount').text = str(inhabitants(sad, happy))
		self.widget.child_finder('happy_amount').text = str(inhabitants(happy))

		# refresh the summary
		self.widget.child_finder('house_count').text = str(houses)
		self.widget.child_finder('resident_count').text = str(residents)

		self.widget.adaptLayout()
		super().refresh()

	def toggle_upgrades(self):
		SetSettlementUpgradePermissions(self.settlement, self.__class__.LEVEL, not self.settlement.upgrade_permissions[self.__class__.LEVEL]).execute(self.settlement.session)


class MainSquareSailorsTab(MainSquareSettlerLevelTab):
	LEVEL = TIER.SAILORS


class MainSquarePioneersTab(MainSquareSettlerLevelTab):
	LEVEL = TIER.PIONEERS


class MainSquareSettlersTab(MainSquareSettlerLevelTab):
	LEVEL = TIER.SETTLERS


class MainSquareCitizensTab(MainSquareSettlerLevelTab):
	LEVEL = TIER.CITIZENS


class MainSquareMerchantsTab(MainSquareSettlerLevelTab):
	LEVEL = TIER.MERCHANTS
