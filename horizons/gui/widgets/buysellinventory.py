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

from fife.extensions import pychan

from fife.extensions.pychan.widgets.common import BoolAttr

from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton


# TOOO:
# This is mostly a copy of Inventory.
# Unify wherever possible.

class BuySellInventory(pychan.widgets.Container):
	"""The buy/sell inventory widget is used to display a stock of items where the available resources are restricted.
	It makes use of the ImageFillStatusButton to display the icons for resources and the fill bar.
	It can be used like any other widget inside of xmls, but for full functionality the inventory
	has to be manually set, or use the TabWidget, which will autoset it (was made to be done this way).

	XML use: <buysellinventory />, can take all the parameters that pychan.widgets.Container can."""
	ATTRIBUTES = pychan.widgets.Container.ATTRIBUTES + [BoolAttr('uncached')]
	# uncached; required when resource icons should appear multiple times at any given moment
	# on the screen. this is usually not the case with single inventories, but e.g. for trading.
	ITEMS_PER_LINE = 4 # TODO: make this a xml attribute with a default value
	def __init__(self, uncached=False, **kwargs):
		# this inits the gui part of the inventory. @see init().
		super(BuySellInventory, self).__init__(**kwargs)
		self._inventory = None
		self.__inited = False
		self.uncached = uncached

	def init(self, db, inventory, limits, selling):
		if not self.__inited or self._inventory is not inventory or \
		   self._limits != limits or self._selling != selling:
			self.__inited = True
			self.db = db
			self._inventory = inventory
			self._limits = limits
			self._selling = selling
			self.__icon = pychan.widgets.Icon(image="content/gui/icons/ship/civil_16.png")
		self.update()

	def update(self):
		assert self.__inited
		self._draw()

	def _draw(self):
		"""Draws the inventory."""
		if len(self.children) != 0:
			self.removeChildren(*self.children)
		vbox = pychan.widgets.VBox(padding = 0)
		vbox.width = self.width
		current_hbox = pychan.widgets.HBox(padding = 0)
		index = 0
		for resid, limit in sorted(self._limits.iteritems()):
			amount = max(0, self._inventory[resid] - limit) if self._selling else max(0, limit - self._inventory[resid])
			# check if this res should be displayed
			button = ImageFillStatusButton.init_for_res(self.db, resid, amount, \
			                                            filled=0, uncached=self.uncached)
			current_hbox.addChild(button)

			if index % self.ITEMS_PER_LINE == (self.ITEMS_PER_LINE - 1) and index != 0:
				vbox.addChild(current_hbox)
				current_hbox = pychan.widgets.HBox(padding = 0)
			index += 1
		vbox.addChild(current_hbox)
		self.addChild(vbox)
		label = pychan.widgets.Label()
		#xgettext:python-format
		label.text = _('Limit: {amount}t per slot').format(amount=self._inventory.get_limit(None))
		label.position = (110, 150)
		self.__icon.position = (90, 150)
		self.addChildren(label, self.__icon)
		self.adaptLayout()
		self.stylize('menu_black')
