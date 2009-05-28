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

from horizons.world.storage import GenericStorage

class Inventory(pychan.widgets.Container):
	"""The inventory widget is used to display a stock of items, namely a Storage class instance.
	It makes use of the ImageFillStatusButton to display the icons for resources and the fill bar.
	It can be used like any other widget inside of xml's, but for full functionality the inventory
	has to be manually set, or use the TabWidget, which will autoset it (was made to be done this way).

	XML use: <inventory />, can take all the parameters that pychan.widgets.Container can."""
	icon_width = 50 # pixels a resource icon is wide

	def __init__(self, **kwargs):
		super(Inventory, self).__init__(**kwargs)
		self._inventory = None

	def _set_inventory(self, inv):
		"""Sets the inventory
		@var inventory: Storage class inventory"""
		assert(isinstance(inv, GenericStorage))
		self._inventory = inv
		self._draw()

	def _get_inventory(self):
		return self._inventory

	inventory = property(_get_inventory, _set_inventory)

	def _draw(self):
		"""Draws the inventory."""
		if len(self.children) is not 0:
			self.removeChildren(*self.children)
		vbox = pychan.widgets.VBox(padding = 0)
		vbox.width = self.width
		current_hbox = pychan.widgets.HBox(padding = 0)
		index = 0
		for resid, amount in self._inventory._storage.iteritems():
			icon, icon_disabled = horizons.main.db('SELECT icon, CASE WHEN (icon_disabled is null) THEN icon ELSE icon_disabled END from data.resource WHERE rowid=?', resid)[0]
			button = ImageFillStatusButton(up_image=icon_disabled if amount == 0 else icon,
										   down_image=icon_disabled if amount == 0 else icon,
										   hover_image=icon_disabled if amount == 0 else icon,
										   text=str(amount),
										   size=(50, 50),
										   res_id = resid,
										   opaque=False)
			button.filled = int(float(amount)/float(self._inventory.limit)*100.0)
			current_hbox.addChild(button)
			if index % (vbox.width/(self.__class__.icon_width+10)) == 0 and  index is not 0:
				vbox.addChild(current_hbox)
				current_hbox = pychan.widgets.HBox(padding=0)
			index += 1
		vbox.addChild(current_hbox)
		self.addChild(vbox)
		self.stylize('menu')

class ImageFillStatusButton(pychan.widgets.Container):

	def __init__(self, up_image, down_image, hover_image, text, res_id, **kwargs):
		"""Represents the image in the ingame gui, with a bar to show how full the inventory is for that resource
		Derives from pychan.widgets.Container, but also takes the args of the pychan.widgets.Imagebutton,
		in order to display the image. The container is only used, because ImageButtons can't have children.
		This is ment to be used with the Inventory widget."""
		super(ImageFillStatusButton, self).__init__(**kwargs)
		self.up_image, self.down_image, self.hover_image, self.text = up_image, down_image, hover_image, text
		self._filled = 0
		self.res_id = res_id

	def _set_filled(self, percent):
		""""@var percent: int percent that fillstatus will be green"""
		self._filled = percent
		self._draw()

	def _get_filled(self):
		return self._filled

	filled = property(_get_filled, _set_filled)

	def _draw(self):
		"""Draws the icon + bar."""
		self.button = pychan.widgets.ImageButton(text=unicode(self.text),
												 up_image=self.up_image,
												 down_image=self.down_image,
												 hover_image=self.hover_image)
		self.button.size = (50, 50)
		bar = pychan.widgets.Icon("content/gui/tab_widget/green_line.png")
		bar.position = (self.button.width-bar.width-1, self.button.height-int(self.button.height/100.0*self._filled))
		self.addChildren(self.button, bar)
