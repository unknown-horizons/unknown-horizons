# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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

from fife.extensions.pychan.widgets import HBox, Icon

from horizons.gui.tabs.tabinterface import TabInterface
from horizons.i18n import _lazy
from horizons.extscheduler import ExtScheduler
from horizons.component.storagecomponent import StorageComponent

class InventoryTab(TabInterface):
	widget = 'island_inventory.xml'
	icon_path = 'icons/tabwidget/common/inventory'
	helptext = _lazy("Settlement inventory")

	lazy_loading = True

	def __init__(self, instance=None):
		self.instance = instance
		super(InventoryTab, self).__init__()

	def init_widget(self):
		boxes = self.widget.child_finder('boxes')
		# TODO magic numbers everywhere here
		for i in xrange(5):
			hbox = HBox(padding=5, min_size=(215, 50), max_size=(215, 50))
			hbox.position = (0, i * 50)
			for j in xrange(4):
				hbox.addChild(Icon(image="content/gui/images/background/inv_bg.png"))
			boxes.addChild(hbox)

		self.widget.child_finder('inventory').init(self.instance.session.db,
		                                           self.instance.get_component(StorageComponent).inventory)

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		self.widget.child_finder('inventory').update()

	def show(self):
		# run once now
		ExtScheduler().add_new_object(self.refresh, self, run_in=0, loops=1)
		# and every sec later
		ExtScheduler().add_new_object(self.refresh, self, run_in=1, loops=-1)
		super(InventoryTab, self).show()

	def hide(self):
		ExtScheduler().rem_call(self, self.refresh)
		super(InventoryTab, self).hide()
