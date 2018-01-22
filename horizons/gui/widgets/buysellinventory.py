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

from fife.extensions.pychan.widgets import HBox

from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton
from horizons.gui.widgets.inventory import Inventory


class BuySellInventory(Inventory):
	"""The buy/sell inventory widget displays an inventory of goods
	where the available resources are restricted. It makes use of the
	ImageFillStatusButton to display resource icons and the fill bar.
	It can be used like any other widget in xml files, but for full
	functionality the inventory has to be manually set, or use the
	TabWidget, which will autoset it (was made to be done this way).

	XML use: <BuySellInventory />, can take all parameters of an Inventory.
	Note that BuySellInventory has False as default value for display_legend
	where Inventory has True.
	"""
	def __init__(self, display_legend=False, **kwargs):
		super().__init__(display_legend=display_legend, **kwargs)

	def init(self, db, inventory, limits, selling):
		if self.init_needed(inventory, limits, selling):
			self._inited = True
			self.db = db
			self._inventory = inventory

			# Specific to BuySellInventory
			self._limits = limits
			self._selling = selling

		self.update()

	def init_needed(self, inventory, limits, selling):
		return super().init_needed(inventory) or \
		       self._limits != limits or self._selling != selling

	def _draw(self, vbox, current_hbox, index=0):
		"""Draws the inventory."""
		for resid, limit in sorted(self._limits.items()):
			if self._selling:
				amount = max(0, self._inventory[resid] - limit)
			else:
				amount = max(0, limit - self._inventory[resid])

			# check if this res should be displayed
			button = ImageFillStatusButton.init_for_res(self.db, resid, amount,
			                                            filled=0, uncached=self.uncached)
			button.button.name = "buy_sell_inventory_{}_entry_{}".format(self._selling, index) # for tests
			current_hbox.addChild(button)

			if index % self.items_per_line == self.items_per_line - 1:
				vbox.addChild(current_hbox)
				current_hbox = HBox(padding=0)
			index += 1
		vbox.addChild(current_hbox)
		self.addChild(vbox)
