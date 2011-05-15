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

from fife.extensions import pychan

from fife.extensions.pychan.widgets.common import BoolAttr

from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton
from horizons.gui.widgets import ProgressBar
from horizons.world.storage import TotalStorage, PositiveSizedSlotStorage

class Inventory(pychan.widgets.Container):
	"""The inventory widget is used to display a stock of items, namely a Storage class instance.
	It makes use of the ImageFillStatusButton to display the icons for resources and the fill bar.
	It can be used like any other widget inside of xmls, but for full functionality the inventory
	has to be manually set, or use the TabWidget, which will autoset it (was made to be done this way).

	XML use: <inventory />, can take all the parameters that pychan.widgets.Container can."""
	ATTRIBUTES = pychan.widgets.Container.ATTRIBUTES + [BoolAttr('uncached')]
	# uncached; required when resource icons should appear multiple times at any given moment
	# on the screen. this is usually not the case with single inventories, but e.g. for trading.
	ITEMS_PER_LINE = 4 # TODO: make this a xml attribute with a default value
	def __init__(self, uncached=False, **kwargs):
		# this inits the gui part of the inventory. @see init().
		super(Inventory, self).__init__(**kwargs)
		self._inventory = None
		self.__inited = False
		self.uncached = uncached

	def init(self, db, inventory):
		# this inits the logic of the inventory. @see __init__().
		self.__inited = True
		self.db = db
		self._inventory = inventory
		self.__icon = pychan.widgets.Icon("content/gui/icons/ship/civil_16.png")
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
		for resid, amount in sorted(self._inventory): # sort by resid for unchangeable positions
			# check if this res should be displayed
			if not self.db.cached_query('SELECT shown_in_inventory FROM resource WHERE id = ?', resid)[0][0]:
				continue

			if isinstance(self._inventory, TotalStorage):
				filled = 0
			else:
				filled = int(float(amount) / float(self._inventory.get_limit(resid)) * 100.0)
			button = ImageFillStatusButton.init_for_res(self.db, resid, amount, \
			                                            filled=filled, uncached=self.uncached)
			current_hbox.addChild(button)

			# old code to do this, which was bad but kept for reference
			#if index % ((vbox.width/(self.__class__.icon_width + 10))) < 0 and index != 0:
			if index % self.ITEMS_PER_LINE == (self.ITEMS_PER_LINE - 1) and index != 0:
				vbox.addChild(current_hbox)
				current_hbox = pychan.widgets.HBox(padding = 0)
			index += 1
		if (index <= self.ITEMS_PER_LINE): # Hide/Remove second line
			icons = self.parent.findChildren(name='slot')
			if len(icons) > self.ITEMS_PER_LINE:
				self.parent.removeChildren(icons[self.ITEMS_PER_LINE-1:])
		vbox.addChild(current_hbox)
		self.addChild(vbox)
		if isinstance(self._inventory, TotalStorage):
			# Add total storage indicator
			sum_stored_res = self._inventory.get_sum_of_stored_resources()
			label = pychan.widgets.Label()
			label.text = unicode(sum_stored_res) + u"/" + unicode(self._inventory.get_limit(None))
			label.position = (170, 50)
			self.__icon.position = (150, 50)
			self.addChildren(label, self.__icon)
		elif isinstance(self._inventory, PositiveSizedSlotStorage):
			label = pychan.widgets.Label()
			label.text = _('Limit: %st per slot') % self._inventory.get_limit(None)
			label.position = (110, 150)
			self.__icon.position = (90, 150)
			self.addChildren(label, self.__icon)
		self.adaptLayout()
		self.stylize('menu_black')