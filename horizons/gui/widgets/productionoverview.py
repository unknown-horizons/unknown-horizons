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

from operator import itemgetter

from fife.extensions.pychan import widgets

from horizons.constants import GAME_SPEED
from horizons.gui.widgets.statswidget import StatsWidget
from horizons.scheduler import Scheduler
from horizons.util.python import decorators
from horizons.gui.util import create_resource_icon
from horizons.util import Callback
from horizons.component.namedcomponent import NamedComponent
from horizons.gui.widgets import OkButton

class ProductionOverview(StatsWidget):
	"""
	Widget that shows every produced resource in this game.

	Implementation based on http://trac.unknown-horizons.org/t/ticket/749 .
	"""

	widget_file_name = 'island_production.xml'

	def __init__(self, settlement):
		super(ProductionOverview, self).__init__(settlement.session)
		self.settlement = settlement
		self.db = self.settlement.session.db
		Scheduler().add_new_object(Callback(self._refresh_tick), self, run_in=GAME_SPEED.TICKS_PER_SECOND, loops=-1)

	def _init_gui(self):
		super(ProductionOverview, self)._init_gui()
		self.session.gui.on_escape = self.hide
		self._gui.findChild(name=OkButton.DEFAULT_NAME).capture(self.hide)

	def hide(self):
		super(ProductionOverview, self).hide()
		self.session.gui.on_escape = self.session.gui.toggle_pause

	def refresh(self):
		super(ProductionOverview, self).refresh()
		#xgettext:python-format
		name = self.settlement.get_component(NamedComponent).name
		text = _('Production overview of {settlement}').format(settlement=name)
		self._gui.findChild(name='headline').text = text

		data = sorted(self.settlement.produced_res.items(), key=itemgetter(1), reverse=True)
		for resource_id, amount in data:
			self._add_line_to_gui(resource_id, amount)
		self._content_vbox.adaptLayout()

	def _add_line_to_gui(self, resource_id, amount, show_all=False):
		displayed = self.db.get_res_inventory_display(resource_id)
		if not displayed:
			return
		res_name = self.db.get_res_name(resource_id)

		icon = create_resource_icon(resource_id, self.db)
		icon.name = 'icon_%s' % resource_id
		icon.max_size = icon.min_size = icon.size = (20, 20)

		label = widgets.Label(name = 'resource_%s' % resource_id)
		label.text = res_name
		label.min_size = (100, 20)

		amount_label = widgets.Label(name = 'produced_sum_%s' % resource_id)
		amount_label.text = unicode(amount)

		hbox = widgets.HBox()
		hbox.addChild(icon)
		hbox.addChild(label)
		hbox.addChild(amount_label)
		self._content_vbox.addChild(hbox)

decorators.bind_all(ProductionOverview)
