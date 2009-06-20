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
import horizons.main
from tabinterface import TabInterface
from horizons.i18n import load_xml_translated

class BoatbuilderTab(TabInterface):

	def __init__(self, instance = None, widget = 'tab_widget/boatbuilder.xml'):
		super(BoatbuilderTab, self).__init__(widget = widget)
		self.instance = instance
		self.init_values()
		events = {
			'createUnit': pychan.tools.callbackWithArguments(self.instance.produce, 15)
		}
		self.widget.mapEvents(events)
		self.button_up_image = 'content/gui/images/icons/hud/common/work_u.png'
		self.button_active_image = 'content/gui/images/icons/hud/common/work_a.png'
		self.button_down_image = 'content/gui/images/icons/hud/common/work_d.png'
		self.button_hover_image = 'content/gui/images/icons/hud/common/work_h.png'

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		self.widget.findChild(name='progress').progress = self.instance.progress

	def show(self):
		if not self.instance.inventory.hasChangeListener(self.refresh):
			self.instance.inventory.addChangeListener(self.refresh)
		super(BoatbuilderTab, self).show()

	def hide(self):
		self.instance.inventory.removeChangeListener(self.refresh)
		super(BoatbuilderTab, self).hide()