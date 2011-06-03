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

from horizons.i18n import load_xml_translated
from horizons.util import Callback
from fife.extensions.pychan import widgets

from horizons.gui.utility import create_resource_icon
from horizons.util.changelistener import metaChangeListenerDecorator


@metaChangeListenerDecorator("pause_request")
@metaChangeListenerDecorator("unpause_request")
class ProductionOverview(object):
	"""
	Widget that shows every produced resource in this game. Allows to toggle
	view between 'settlement' and 'player' similar to the exchange tab.

	Implementation based on http://trac.unknown-horizons.org/t/ticket/749 .
	"""
	def __init__(self, settlement):
		self.settlement = settlement
		self.db = self.settlement.session.db
		self.player = self.settlement.owner

		self._init_gui()

	def show(self):
		self._gui.show()
		self.on_pause_request()

	def hide(self):
		self._gui.hide()
		self.on_unpause_request()

	def refresh(self):
		self._clear_entries()
		for (res, amount) in self._sort_resources_by_amount(self.settlement.produced_res):
			self._add_resource_line_to_gui(self._gui.findChild(name='resources_vbox'), res, amount)

	def is_visible(self):
		return self._gui.isVisible()

	def toggle_visibility(self):
		if self.is_visible():
			self.hide()
		else:
			self.show()

	def _add_resource_line_to_gui(self, gui, res_id, amount=0, show_all=False):
		# later we will modify which resources to be displayed (e.g. all
		# settlements) via the switch show_all
		res_name = self.db.get_res_name(res_id, only_if_inventory=True)
		# above code returns None if not shown in inventories
		displayed = (res_name is not None) or show_all
		if displayed:
			icon = create_resource_icon(res_id, self.db, size=16)
			icon.name = 'icon_%s' % res_id
			label = widgets.Label(name='resource_%s' % res_id)
			label.text = unicode(res_name)
			amount_label = widgets.Label(name='produced_sum_%s' % res_id)
			amount_label.text = unicode(amount)
			hbox = widgets.HBox()
			hbox.addChild(icon)
			hbox.addChild(label)
			hbox.addChild(amount_label)
			gui.addChild(hbox)
			gui.adaptLayout()

	def _init_gui(self):
		"""
		Initial init of gui.
		resource_entries : dict of all resources and their respective values
		                   that will be displayed
		"""
		self._gui = load_xml_translated("island_production.xml")
		self._gui.mapEvents({
		  'cancelButton' : self.hide,
		  'refreshButton' : self.refresh
		  })
		self._gui.position_technique = "automatic" # "center:center"

		self.backward_button = self._gui.findChild(name="backwardButton")
		self.forward_button = self._gui.findChild(name="forwardButton")
		self.refresh()

	def _clear_entries(self):
		"""Removes all information. Called when refreshing or when changing
		display mode (settlement <-> player)."""
		self._gui.findChild(name='resources_vbox').removeAllChildren()

	def _sort_resources_by_amount(self, resource_dict, order='desc'):
		dict_list = [(res, resource_dict.get(res, 0)) for res in resource_dict.keys()]
		sorted_values = sorted(dict_list, key=lambda res: res[1], reverse=True)
		return sorted_values
