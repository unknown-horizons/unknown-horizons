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

from fife.extensions import pychan

from horizons.util.gui import load_uh_widget, get_res_icon
from horizons.constants import RES

class TradeHistoryItem(pychan.widgets.Container):
	"""Widget that shows the last few trades that have taken place in the settlement."""

	def __init__(self, player, resource_id, amount, gold, **kwargs):
		super(TradeHistoryItem, self).__init__(**kwargs)
		self.widget = load_uh_widget('trade_history_item.xml')
		self.addChild(self.widget)

		self.findChild(name='player_emblem').background_color = player.color
		self.findChild(name='player_name').text = player.name

		gold_amount_label = self.findChild(name='gold_amount')
		gold_amount_label.text = u'{gold:+5d}'.format(gold=gold)

		gold_icon = self.findChild(name='gold_icon')
		gold_icon.image = get_res_icon(RES.GOLD_ID)[3]
		gold_icon.helptext = player.session.db.get_res_name(RES.GOLD_ID)

		resource_amount_label = self.findChild(name='resource_amount')
		resource_amount_label.text = u'{amount:+5d}'.format(amount=amount)

		resource_icon = self.findChild(name='resource_icon')
		resource_icon.image = get_res_icon(resource_id)[3]
		resource_icon.helptext = player.session.db.get_res_name(resource_id)

		self.size = self.widget.size
