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

from fife.extensions.pychan import widgets

from horizons.constants import GAME_SPEED
from horizons.gui.widgets.statswidget import StatsWidget
from horizons.scheduler import Scheduler
from horizons.util.python import decorators
from horizons.util import Callback

class PlayersSettlements(StatsWidget):
	"""Widget that shows a list of the player's settlements."""

	widget_file_name = 'players_settlements.xml'

	def __init__(self, session):
		super(PlayersSettlements, self).__init__(session)
		Scheduler().add_new_object(Callback(self._refresh_tick), self, run_in = 1, loops = -1, loop_interval = GAME_SPEED.TICKS_PER_SECOND / 3)

	def refresh(self):
		super(PlayersSettlements, self).refresh()
		self._gui.findChild(name = 'headline').text = _('%(player)s\'s settlements') % {'player': self.session.world.player.name}

		sequence_number = 0
		events = {}
		for settlement in self.session.world.settlements:
			if settlement.owner is self.session.world.player:
				sequence_number += 1
				name_label = self._add_line_to_gui(settlement, sequence_number)
				events['%s/mouseClicked' % name_label.name] = Callback(self._go_to_settlement, settlement)
		self._gui.mapEvents(events)
		self._content_vbox.adaptLayout()

	def _go_to_settlement(self, settlement):
		position = settlement.branch_office.position.center()
		self.session.view.center(position.x, position.y)

	def _add_line_to_gui(self, settlement, sequence_number):
		sequence_number_label = widgets.Label(name = 'sequence_number_%d' % settlement.worldid)
		sequence_number_label.text = unicode(sequence_number)
		sequence_number_label.min_size = sequence_number_label.max_size = (15, 20)

		name = widgets.Label(name = 'name_%d' % settlement.worldid)
		name.text = unicode(settlement.name)
		name.min_size = name.max_size = (200, 20)

		inhabitants = widgets.Label(name = 'inhabitants_%d' % settlement.worldid)
		inhabitants.text = unicode(settlement.inhabitants)
		inhabitants.min_size = inhabitants.max_size = (110, 20)

		taxes = widgets.Label(name = 'taxes_%d' % settlement.worldid)
		taxes.text = unicode(settlement.cumulative_taxes)
		taxes.min_size = taxes.max_size = (50, 20)

		running_costs = widgets.Label(name = 'running_costs_%d' % settlement.worldid)
		running_costs.text = unicode(settlement.cumulative_running_costs)
		running_costs.min_size = running_costs.max_size = (100, 20)

		balance = widgets.Label(name = 'balance_%d' % settlement.worldid)
		balance.text = unicode(settlement.cumulative_taxes - settlement.cumulative_running_costs)
		balance.min_size = balance.max_size = (60, 20)

		hbox = widgets.HBox()
		hbox.addChild(sequence_number_label)
		hbox.addChild(name)
		hbox.addChild(inhabitants)
		hbox.addChild(taxes)
		hbox.addChild(running_costs)
		hbox.addChild(balance)
		self._content_vbox.addChild(hbox)
		return name

decorators.bind_all(PlayersSettlements)
