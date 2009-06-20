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
import horizons.main
import pychan
import weakref
from tabinterface import TabInterface

class OverviewTab(TabInterface):

	def __init__(self, instance = None, widget = 'tab_widget/tab_overview.xml'):
		super(OverviewTab, self).__init__(widget)
		self.instance = instance
		instance.addChangeListener(self.refresh)
		self.init_values()
		
	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		if hasattr(self.instance, 'name'):
			self.widget.findChild(name='name').text = unicode(self.instance.name)
		if hasattr(self.instance, 'health'):
			self.widget.findChild(name='health').text = unicode(self.instance.health)
		self.widget._recursiveResizeToContent()

	def show(self):
		super(OverviewTab, self).show()
		if not self.instance.hasChangeListener(self.refresh):
			self.instance.addChangeListener(self.refresh)

	def hide(self):
		super(OverviewTab, self).hide()
		self.instance.removeChangeListener(self.refresh)


class ShipOverviewTab(OverviewTab):

	def __init__(self, instance = None):
		super(ShipOverviewTab, self).__init__(
			widget = 'tab_widget/tab_overview_ship.xml',
			instance = instance
		)
		events = { 'foundSettelment': pychan.tools.callbackWithArguments(horizons.main.session.ingame_gui._build, 1, weakref.ref(instance) )}
		self.widget.mapEvents(events)
		self.button_up_image = 'content/gui/images/icons/hud/common/ship_inv_u.png'
		self.button_active_image = 'content/gui/images/icons/hud/common/ship_inv_a.png'
		self.button_down_image = 'content/gui/images/icons/hud/common/ship_inv_d.png'
		self.button_hover_image = 'content/gui/images/icons/hud/common/ship_inv_h.png'


class ProductionOverviewTab(OverviewTab):

	def  __init__(self, instance = None):
		super(ProductionOverviewTab, self).__init__(
			widget = 'buildings_gui/production_building_overview.xml',
			instance = instance
		)
		events = { 'toggle_active': self.instance.toggle_active }
		self.widget.mapEvents(events)
		self.button_up_image = 'content/gui/images/icons/hud/common/dummy_40_a.png'
		self.button_active_image = 'content/gui/images/icons/hud/common/dummy_40_a.png'
		self.button_down_image = 'content/gui/images/icons/hud/common/dummy_40_a.png'
		self.button_hover_image = 'content/gui/images/icons/hud/common/dummy_40_a.png'


	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		if hasattr(self.instance, 'running_costs'):
			self.widget.findChild(name='running_costs').text = unicode(self.instance.running_costs)
		super(ProductionOverviewTab, self).refresh()



