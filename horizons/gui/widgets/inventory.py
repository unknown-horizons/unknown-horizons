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

from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton

class Inventory(pychan.widgets.Container):
	"""The inventory widget is used to display a stock of items, namely a Storage class instance.
	It makes use of the ImageFillStatusButton to display the icons for resources and the fill bar.
	It can be used like any other widget inside of xmls, but for full functionality the inventory
	has to be manually set, or use the TabWidget, which will autoset it (was made to be done this way).

	XML use: <inventory />, can take all the parameters that pychan.widgets.Container can."""
	icon_width = 50 # pixels a resource icon is wide

	def __init__(self, **kwargs):
		super(Inventory, self).__init__(**kwargs)
		self._inventory = None

	def _set_inventory(self, inv):
		"""Sets the inventory
		@var inventory: Storage class inventory"""
		assert(isinstance(inv, horizons.world.storage.GenericStorage))
		self._inventory = inv
		self._draw()

	def _get_inventory(self):
		return self._inventory

	inventory = property(_get_inventory, _set_inventory)

	def _draw(self):
		"""Draws the inventory."""
		if len(self.children) != 0:
			self.removeChildren(*self.children)
		vbox = pychan.widgets.VBox(padding = 0)
		vbox.width = self.width
		current_hbox = pychan.widgets.HBox(padding = 0)
		index = 0
		for resid, amount in self.inventory:
			# check if this res should be displayed
			if not horizons.main.db('SELECT shown_in_inventory FROM resource WHERE id = ?', resid)[0][0]:
				continue
			icon, icon_disabled = horizons.main.db('SELECT icon, CASE WHEN (icon_disabled is null) THEN icon ELSE icon_disabled END from data.resource WHERE id=?', resid)[0]
			tooltip = horizons.main.db('SELECT name FROM data.resource WHERE id = ?', resid)[0][0]
			button = ImageFillStatusButton(up_image=icon_disabled if amount == 0 else icon,
										   down_image=icon_disabled if amount == 0 else icon,
										   hover_image=icon_disabled if amount == 0 else icon,
										   text=str(amount),
			                 tooltip=tooltip,
										   size=(55, 50),
										   res_id = resid,
										   opaque=False)
			button.filled = int(float(amount) / float(self._inventory.limit) * 100.0)
			current_hbox.addChild(button)
			if index % (vbox.width/(self.__class__.icon_width + 10)) == 0 and  index is not 0:
				vbox.addChild(current_hbox)
				current_hbox = pychan.widgets.HBox(padding = 0)
			index += 1
		vbox.addChild(current_hbox)
		self.addChild(vbox)
		self.adaptLayout()
		self.stylize('menu_black')

