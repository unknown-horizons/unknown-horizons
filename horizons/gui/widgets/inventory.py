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

from fife.extensions.pychan.widgets.common import BoolAttr, IntAttr

from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton
from horizons.world.storage import TotalStorage, PositiveSizedSlotStorage, PositiveTotalNumSlotsStorage

class Inventory(pychan.widgets.Container):
	"""The inventory widget is used to display a stock of items, namely a Storage class instance.
	It makes use of the ImageFillStatusButton to display the icons for resources and the fill bar.
	It can be used like any other widget inside of xmls, but for full functionality the inventory
	has to be manually set, or use the TabWidget, which will autoset it (was made to be done this way).

	XML use: <Inventory />, can take all the parameters that pychan.widgets.Container can."""
	ATTRIBUTES = pychan.widgets.Container.ATTRIBUTES + [BoolAttr('uncached'), BoolAttr('display_legend'), IntAttr("items_per_line")]
	# uncached: required when resource icons should appear multiple times at any given moment
	# on the screen. this is usually not the case with single inventories, but e.g. for trading.
	# display_legend: whether to display a string explanation about slot limits

	UNUSABLE_SLOT_IMAGE = "content/gui/icons/resources/none_gray.png"

	def __init__(self, uncached=False, display_legend=True, items_per_line=4, **kwargs):
		# this inits the gui part of the inventory. @see init().
		super(Inventory, self).__init__(**kwargs)
		self._inventory = None
		self.__inited = False
		self.uncached = uncached
		self.display_legend = display_legend
		self.items_per_line = items_per_line or 1 # negative values are fine, 0 is not

	def init(self, db, inventory, ordinal=None):
		"""
		@param ordinal: {res: (min, max)} Display ordinal scale with these boundaries instead of numbers for a particular resource. Currently implemented via ImageFillStatusButton.
		"""
		# check if we must init everything anew
		if not self.__inited or self._inventory is not inventory:
			# this inits the logic of the inventory. @see __init__().
			self.__inited = True
			self.ordinal = ordinal
			self.db = db
			self._inventory = inventory
			self._res_order = sorted(self._inventory.iterslots())
			self.__icon = pychan.widgets.Icon(image="content/gui/icons/ship/civil_16.png")
		self.update()

	def update(self):
		assert self.__inited
		self._draw()

	def _draw(self):
		"""Draws the inventory."""
		self.removeAllChildren()
		vbox = pychan.widgets.VBox(padding=0)
		vbox.width = self.width
		current_hbox = pychan.widgets.HBox(padding=0)
		index = 0

		# add res to res order in case there are new ones
		# (never remove old ones for consistent positioning)
		new_res = sorted( resid for resid in self._inventory.iterslots() if resid not in self._res_order )

		if isinstance(self._inventory, PositiveTotalNumSlotsStorage):
			# limited number of slots. We have to switch unused slots with newly added ones on overflow

			while len(self._res_order) + len(new_res) > self._inventory.slotnum:
				for i in xrange( self._inventory.slotnum ):
					# search empty slot
					if self._inventory[ self._res_order[i] ] == 0:
						# insert new res here
						self._res_order[i] = new_res.pop(0)
						if not new_res:
							break # all done

		# add remaining slots for slotstorage or just add it without consideration for other storage kinds
		self._res_order += new_res

		for resid in self._res_order:
			# check if this res should be displayed
			if not self.db.cached_query('SELECT shown_in_inventory FROM resource WHERE id = ?', resid)[0][0]:
				continue

			amount = self._inventory[resid]

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
				current_hbox = pychan.widgets.HBox(padding=0)
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
			if self._inventory.get_free_space_for(0) == 0:
				for i in xrange(index, self.items_per_line):
					button = pychan.widgets.Icon(image=self.__class__.UNUSABLE_SLOT_IMAGE)
					current_hbox.addChild(button)


		if self.display_legend:
			if isinstance(self._inventory, TotalStorage):
				# Add total storage indicator
				sum_stored_res = self._inventory.get_sum_of_stored_resources()
				label = pychan.widgets.Label()
				label.text = unicode(sum_stored_res) + u"/" + unicode(self._inventory.get_limit(None))
				label.position = (150, 53)
				self.__icon.position = (130, 53)
				self.addChildren(label, self.__icon)
			elif isinstance(self._inventory, PositiveSizedSlotStorage):
				label = pychan.widgets.Label()
				#xgettext:python-format
				label.text = _('Limit: {amount}t per slot').format(amount=self._inventory.get_limit(None))
				label.position = (20, 203)
				self.__icon.position = (0, 203)
				self.addChildren(label, self.__icon)
		self.adaptLayout()
		self.stylize('menu_black')

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
				if filt == None or filt(widget):
					action(widget)
		self.deepApply(_find_widget)
