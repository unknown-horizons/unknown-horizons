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

from tabinterface import TabInterface

class AccountTab(TabInterface):
	"""Display basic income and expenses of a settlement"""

	def __init__(self, instance):
		super(AccountTab, self).__init__(widget = 'tab_widget/tab_account.xml')
		self.settlement = instance.settlement
		self.init_values()
		self.button_up_image = 'content/gui/images/icons/hud/common/account_u.png'
		self.button_active_image = 'content/gui/images/icons/hud/common/account_a.png'
		self.button_down_image = 'content/gui/images/icons/hud/common/account_d.png'
		self.button_hover_image = 'content/gui/images/icons/hud/common/account_h.png'

	def refresh(self):
		taxes = self.settlement.cumulative_taxes
		running_costs = self.settlement.cumulative_running_costs
		buy_expenses = self.settlement.buy_expenses
		sell_income = self.settlement.sell_income
		balance = taxes - running_costs - buy_expenses + sell_income
		sign = '+' if balance >= 0 else '-'
		self.widget.child_finder('taxes').text = unicode(taxes)
		self.widget.child_finder('running_costs').text = unicode(running_costs)
		self.widget.child_finder('buying').text = unicode(buy_expenses)
		self.widget.child_finder('sale').text = unicode(sell_income)
		self.widget.child_finder('balance').text = unicode(sign+' '+str(abs(balance)))

	def show(self):
		super(AccountTab, self).show()
		# update self when a building of the settlement changes.
		for building in self.settlement.buildings:
			if not building.has_change_listener(self.refresh):
				building.add_change_listener(self.refresh)

	def hide(self):
		super(AccountTab, self).hide()
		for building in self.settlement.buildings:
			if building.has_change_listener(self.refresh):
				building.remove_change_listener(self.refresh)
