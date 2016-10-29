# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

from fife.extensions.pychan.widgets import Container, HBox, Icon, Label, VBox
from fife.extensions.pychan.widgets.common import BoolAttr, IntAttr

from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton
from horizons.i18n import gettext as _
from horizons.world.storage import (
	PositiveSizedSlotStorage, PositiveTotalNumSlotsStorage, TotalStorage)


class Inventory(Container):
	"""The inventory widget displays information about the goods in
	a Storage. It uses ImageFillStatusButtons to display icons and
	a fill bar for these resources.
	It can be used like any other widget in xml files, but for full
	functionality the inventory has to be manually set, or use the
	TabWidget, which will autoset it (was made to be done this way).

	XML use: <Inventory />, can take all parameters of a Container.
	"""
	ATTRIBUTES = Container.ATTRIBUTES + [BoolAttr('uncached'),
	                                     BoolAttr('display_legend'),
	                                     IntAttr("items_per_line")]
	# uncached: required when resource icons should appear multiple times at any given moment
	# on the screen. this is usually not the case with single inventories, but e.g. for trading.
	# display_legend: whether to display a string explanation about slot limits

	UNUSABLE_SLOT_IMAGE = "content/gui/icons/resources/none_gray.png"

	def __init__(self, uncached=False, display_legend=True, items_per_line=4, **kwargs):
		# this inits the gui part of the inventory. @see init().
		super(Inventory, self).__init__(**kwargs)
		self._inventory = None
		self._inited = False
		self.uncached = uncached
		self.display_legend = display_legend
		self.items_per_line = items_per_line or 1 # negative values are fine, 0 is not

	def init_needed(self, inventory):
		return not self._inited or self._inventory is not inventory

	def init(self, db, inventory, ordinal=None):
		"""This inits the logic of the inventory. @see __init__().
		@param ordinal: {res: (min, max)} Display ordinal scale with these boundaries instead of numbers for a particular resource. Currently implemented via ImageFillStatusButton.
		"""
		# check if we must init everything anew
		if self.init_needed(inventory):
			self._inited = True
			self.db = db
			self._inventory = inventory

			# specific to Inventory
			self.ordinal = ordinal
			self._res_order = sorted(self._inventory.iterslots())
			self.legend = Label(name="legend")
			self.__icon = Icon(name="legend_icon")
			self.__icon.image = "content/gui/icons/ship/civil_16.png"
			if isinstance(self._inventory, TotalStorage):
				self.__icon.position = (130, 53)
				self.legend.position = (150, 53)
			elif isinstance(self._inventory, PositiveSizedSlotStorage):
				self.__icon.position = ( 0, 248)
				self.legend.position = (20, 248)

		self.update()

	def update(self):
		self.removeAllChildren()
		if self.display_legend:
			self.addChildren(self.__icon, self.legend)
		vbox = VBox(padding=0)
		vbox.width = self.width
		current_hbox = HBox(padding=0)

		# draw the content
		self._draw(vbox, current_hbox)

		self.adaptLayout()

	def _draw(self, vbox, current_hbox, index=0):
		"""Draws the inventory."""
		# add res to res order in case there are new ones
		# (never remove old ones for consistent positioning)
		new_res = sorted( resid for resid in self._inventory.iterslots() if resid not in self._res_order )

		if isinstance(self._inventory, PositiveTotalNumSlotsStorage):
			# limited number of slots. We have to switch unused slots with newly added ones on overflow

			while len(self._res_order) + len(new_res) > self._inventory.slotnum:
				for i in xrange(self._inventory.slotnum):
					if len(self._res_order) <= i or self._inventory[self._res_order[i]]:
						# search empty slot
						continue
					# insert new res here
					self._res_order[i] = new_res.pop(0)
					if not new_res:
						break # all done

		# add remaining slots for slotstorage or just add it without consideration for other storage kinds
		self._res_order += new_res

		for resid in self._res_order:
			amount = self._inventory[resid]
			if amount == 0:
				index += 1
				continue

			# check if this res should be displayed
			if not self.db.cached_query('SELECT shown_in_inventory FROM resource WHERE id = ?', resid)[0][0]:
				continue

			if self.ordinal:
				lower, upper = self.ordinal.get(resid, (0, 100))
				filled = (100 * (amount - lower)) // (upper - lower)
				amount = "" # do not display exact information for resource deposits
			elif isinstance(self._inventory, TotalStorage):
				filled = 0
			else:
				filled = (100 * amount) // self._inventory.get_limit(resid)

			button = ImageFillStatusButton.init_for_res(self.db, resid, amount,
			                                            filled=filled, uncached=self.uncached)
			button.button.name = "inventory_entry_%s" % index # required for gui tests
			current_hbox.addChild(button)

			if index % self.items_per_line == self.items_per_line - 1:
				vbox.addChild(current_hbox)
				current_hbox = HBox(padding=0)
			index += 1
		if index <= self.items_per_line: # Hide/Remove second line
			icons = self.parent.findChildren(name='slot')
			if len(icons) > self.items_per_line:
				self.parent.removeChildren(icons[self.items_per_line-1:])
		vbox.addChild(current_hbox)
		self.addChild(vbox)
		height = ImageFillStatusButton.CELL_SIZE[1] * len(self._res_order) // self.items_per_line
		self.min_size = (self.min_size[0], height)

		if isinstance(self._inventory, TotalStorage):
			# if it's full, the additional slots have to be marked as unusable (#1686)
			# check for any res, the res type doesn't matter here
			if not self._inventory.get_free_space_for(0):
				for i in xrange(index, self.items_per_line):
					button = Icon(image=self.__class__.UNUSABLE_SLOT_IMAGE)
					# set min & max_size to prevent pychan to expand this dynamic widget (icon)
					button.min_size = button.max_size = ImageFillStatusButton.ICON_SIZE
					current_hbox.addChild(button)

		if self.display_legend:
			limit = self._inventory.get_limit(None)
			if isinstance(self._inventory, TotalStorage):
				# Add total storage indicator
				sum_stored = self._inventory.get_sum_of_stored_resources()
				self.legend.text = _('{stored}/{limit}').format(stored=sum_stored, limit=limit)
			elif isinstance(self._inventory, PositiveSizedSlotStorage):
				self.legend.text = _('Limit: {amount}t per slot').format(amount=limit)

	def apply_to_buttons(self, action, filt=None):
		"""Applies action to all buttons shown in inventory
		@param action: function called that touches button
		@param filt: function used to filter the buttons
		both functions take one parameter which is the button
		"""
		if filt:
			assert callable(filt)
		assert callable(action)

		def _find_widget(widget):
			if isinstance(widget, ImageFillStatusButton):
				if filt is None or filt(widget):
					action(widget)
		self.deepApply(_find_widget)
