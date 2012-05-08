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

from fife.extensions.pychan import widgets

from fife.extensions.pychan.widgets import ImageButton
from horizons.gui.widgets.statswidget import StatsWidget
from horizons.util.python import decorators
from horizons.util import Callback
from horizons.component.namedcomponent import NamedComponent

class PlayersSettlements(StatsWidget):
	"""Widget that shows a list of the player's settlements."""

	widget_file_name = 'players_settlements.xml'

	def __init__(self, session):
		super(PlayersSettlements, self).__init__(session)

	def refresh(self):
		super(PlayersSettlements, self).refresh()
		#xgettext:python-format
		self._gui.findChild(name = 'headline').text = _("Settlements of {player}").format(player=self.session.world.player.name)

		sequence_number = 0
		events = {}
		for settlement in sorted(self.session.world.settlements, key = lambda settlement: (settlement.get_component(NamedComponent).name, settlement.worldid)):
			if settlement.owner is self.session.world.player:
				sequence_number += 1
				name_label, rename_icon = self._add_line_to_gui(settlement, sequence_number)
				events['%s/mouseClicked' % name_label.name] = Callback(self._go_to_settlement, settlement)
				cb = Callback(self.session.ingame_gui.show_change_name_dialog, settlement)
				events['%s/mouseClicked' % rename_icon.name] = cb
		self._gui.mapEvents(events)
		self._add_summary_line_to_gui()
		self._content_vbox.adaptLayout()

	def _go_to_settlement(self, settlement):
		position = settlement.warehouse.position.center()
		self.session.view.center(position.x, position.y)

	def _add_generic_line_to_gui(self, id, line_prefix, people, tax, costs):
		inhabitants = widgets.Label(name = 'inhabitants_%d' % id)
		inhabitants.text = unicode(people)
		inhabitants.min_size = inhabitants.max_size = (110, 20)

		taxes = widgets.Label(name = 'taxes_%d' % id)
		taxes.text = unicode(tax)
		taxes.min_size = taxes.max_size = (50, 20)

		running_costs = widgets.Label(name = 'running_costs_%d' % id)
		running_costs.text = unicode(costs)
		running_costs.min_size = running_costs.max_size = (100, 20)

		balance = widgets.Label(name = 'balance_%d' % id)
		balance.text = unicode(tax - costs)
		balance.min_size = balance.max_size = (60, 20)

		hbox = widgets.HBox()
		for widget in line_prefix:
			hbox.addChild(widget)
		hbox.addChild(inhabitants)
		hbox.addChild(taxes)
		hbox.addChild(running_costs)
		hbox.addChild(balance)
		self._content_vbox.addChild(hbox)

	def _add_line_to_gui(self, settlement, sequence_number):
		sequence_number_label = widgets.Label(name = 'sequence_number_%d' % settlement.worldid)
		sequence_number_label.text = unicode(sequence_number)
		sequence_number_label.min_size = sequence_number_label.max_size = (15, 20)

		name = widgets.Label(name = 'name_%d' % settlement.worldid)
		name.text = settlement.get_component(NamedComponent).name
		name.min_size = name.max_size = (175, 20)

		rename_icon = ImageButton(name = 'rename_%d' % settlement.worldid)
		rename_icon.up_image = "content/gui/images/background/rename_feather_20.png"
		rename_icon.hover_image = "content/gui/images/background/rename_feather_20_h.png"
		rename_icon.helptext = _("Click to change the name of your settlement")
		rename_icon.max_size = (20, 20) # (width, height)

		self._add_generic_line_to_gui(settlement.worldid, [sequence_number_label, name, rename_icon],
			settlement.inhabitants, settlement.cumulative_taxes, settlement.cumulative_running_costs)
		return name, rename_icon

	def _add_summary_line_to_gui(self):
		people = 0
		tax = 0
		costs = 0
		for settlement in self.session.world.settlements:
			if settlement.owner is self.session.world.player:
				people += settlement.inhabitants
				tax += settlement.cumulative_taxes
				costs += settlement.cumulative_running_costs

		sequence_number_label = widgets.Label(name = 'sequence_number_total')
		sequence_number_label.min_size = sequence_number_label.max_size = (15, 20)

		name = widgets.Label(name = 'name_total')
		name.text = _(u'Total')
		name.min_size = name.max_size = (200, 20)

		self._add_generic_line_to_gui(0, [sequence_number_label, name], people, tax, costs)

decorators.bind_all(PlayersSettlements)
