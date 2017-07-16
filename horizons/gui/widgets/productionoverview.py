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

import math
from operator import itemgetter

from fife.extensions.pychan import widgets

from horizons.component.namedcomponent import NamedComponent
from horizons.constants import GAME_SPEED
from horizons.gui.util import create_resource_icon, load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton
from horizons.gui.widgets.statswidget import StatsWidget
from horizons.gui.windows import Window
from horizons.i18n import gettext as T
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback


class MultiPageStatsWidget(StatsWidget):
	"""
	A widget that creates a large table with statistics that can be browsed through page by
	page.
	"""
	widget_file_name = None # type: str

	def _init_gui(self):
		self._gui = load_uh_widget(self.widget_file_name, center_widget=self.center_widget)
		if not self.center_widget:
			self._gui.position_technique = 'center+20:center+25'
		self._page_left = self._gui.findChild(name='page_left')
		self._page_right = self._gui.findChild(name='page_right')
		self.refresh()

	def _clear_entries(self):
		self._page_left.removeAllChildren()
		self._page_right.removeAllChildren()


class ProductionOverview(MultiPageStatsWidget, Window):
	"""
	Widget that shows every produced resource in this game.

	Implementation based on https://github.com/unknown-horizons/unknown-horizons/issues/749 .
	"""
	LINES_PER_PAGE = 12

	widget_file_name = 'island_production.xml'

	def __init__(self, windows, settlement):
		StatsWidget.__init__(self, settlement.session, center_widget=True)
		Window.__init__(self, windows)

		self.current_page = 0
		self.settlement = settlement
		self.db = self.settlement.session.db
		Scheduler().add_new_object(Callback(self._refresh_tick), self, run_in=GAME_SPEED.TICKS_PER_SECOND, loops=-1)

	def _init_gui(self):
		super()._init_gui()
		self._gui.findChild(name=OkButton.DEFAULT_NAME).capture(self._windows.close)
		self._gui.findChild(name='forwardButton').capture(self.go_to_next_page)
		self._gui.findChild(name='backwardButton').capture(self.go_to_previous_page)

	@property
	def displayed_resources(self):
		"""
		Returns all resources of the settlement that should be shown.
		"""
		data = sorted(self.settlement.produced_res.items(), key=itemgetter(1), reverse=True)
		return [(resource_id, amount) for (resource_id, amount) in data
		        if self.db.get_res_inventory_display(resource_id)]

	@property
	def max_pages(self):
		"""
		Returns number of pages the resources need.
		"""
		# int() and float() wrapping needed?
		return int(math.ceil(len(self.displayed_resources) / float(self.LINES_PER_PAGE)))

	def go_to_next_page(self):
		"""
		Scrolls forward two pages. `self.current_page` will always be the index of the
		left page of the book.
		"""
		self.current_page = min(self.max_pages - 1, self.current_page + 2)
		self.current_page -= self.current_page % 2
		self.refresh()

	def go_to_previous_page(self):
		"""
		Scrolls backward two pages. `self.current_page` will always be the index of the
		left page of the book.
		"""
		self.current_page = max(0, self.current_page - 2)
		self.refresh()

	def refresh(self):
		super().refresh()

		name = self.settlement.get_component(NamedComponent).name
		text = T('Production overview of {settlement}').format(settlement=name)
		self._gui.findChild(name='headline').text = text

		forward_button = self._gui.findChild(name='forwardButton')
		backward_button = self._gui.findChild(name='backwardButton')

		if self.current_page == 0:
			backward_button.set_inactive()
		else:
			backward_button.set_active()

		max_left_page_idx = self.max_pages - 1
		max_left_page_idx -= max_left_page_idx % 2
		if self.current_page == max_left_page_idx:
			forward_button.set_inactive()
		else:
			forward_button.set_active()

		data = self.displayed_resources
		data = data[self.current_page * self.LINES_PER_PAGE:(self.current_page + 2) * self.LINES_PER_PAGE]

		for idx, (resource_id, amount) in enumerate(data, start=1):
			if idx > self.LINES_PER_PAGE:
				container = self._page_right
			else:
				container = self._page_left

			self._add_line_to_gui(container, resource_id, amount)

		self._page_left.adaptLayout()
		self._page_right.adaptLayout()

	def _add_line_to_gui(self, container, resource_id, amount):
		res_name = self.db.get_res_name(resource_id)

		icon = create_resource_icon(resource_id, self.db)
		icon.name = 'icon_{}'.format(resource_id)
		icon.max_size = icon.min_size = icon.size = (20, 20)

		label = widgets.Label(name='resource_{}'.format(resource_id))
		label.text = res_name
		label.min_size = (100, 20)

		amount_label = widgets.Label(name='produced_sum_{}'.format(resource_id))
		amount_label.text = str(amount)

		hbox = widgets.HBox()
		hbox.addChild(icon)
		hbox.addChild(label)
		hbox.addChild(amount_label)
		container.addChild(hbox)
