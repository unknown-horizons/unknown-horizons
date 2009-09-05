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
import pychan
import math

from tabinterface import TabInterface
from horizons.command.production import AddProduction

class BoatbuilderTab(TabInterface):

	def __init__(self, instance = None, widget = 'tab_widget/boatbuilder.xml'):
		super(BoatbuilderTab, self).__init__(widget = widget)
		self.instance = instance
		self.init_values()
		events = { 'createUnit': AddProduction(self.instance, 15).execute }
		self.widget.mapEvents(events)
		self.button_up_image = 'content/gui/images/icons/hud/common/work_u.png'
		self.button_active_image = 'content/gui/images/icons/hud/common/work_a.png'
		self.button_down_image = 'content/gui/images/icons/hud/common/work_d.png'
		self.button_hover_image = 'content/gui/images/icons/hud/common/work_h.png'
		self.tooltip = u"Boat Builder"

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		progress = self.instance.get_production_progress()
		self.widget.findChild(name='progress').progress = progress*100
		self.widget.findChild(name='current_construction_label').text = \
				_("Current construction progress:")+" "+str(math.floor(progress*100))+"%"

	def show(self):
		if not self.instance.inventory.has_change_listener(self.refresh):
			self.instance.inventory.add_change_listener(self.refresh)
		super(BoatbuilderTab, self).show()

	def hide(self):
		self.instance.inventory.remove_change_listener(self.refresh)
		super(BoatbuilderTab, self).hide()
