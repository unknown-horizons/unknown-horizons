# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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
from game.world.storage import Storage
import game.main

class Inventory(pychan.widgets.Container):

	icon_width = 50 # pixels a ressource icon is wide

	def __init__(self, **kwargs):
		super(Inventory,self).__init__(**kwargs)
		self.stylize('menu')
		self._inventory = None

	def _set_inventory(self, inv):
		"""Sets the inventory
		@var inventory: Storage class inventory"""
		print inv
		assert(isinstance(inv, Storage))
		self._inventory = inv
		self._draw()

	def _get_inventory(self):
		return self._inventory

	inventory = property(_get_inventory, _set_inventory)

	def isset_inventory(self):
		"""Returns whether the inventory is set or not"""
		return True if inventory is not None else False

	def _draw(self):
		"""Draws the inventory."""
		vbox = pychan.widgets.VBox()
		vbox._setOpaque(False)
		vbox.width = self.width
		current_hbox = pychan.widgets.HBox()
		current_hbox._setOpaque(False)
		for index, resid in enumerate(self._inventory._inventory.iteritems()):
			print 'found res', resid
			icon = str(game.main.db('SELECT icon from ressource WHERE rowid=?', resid[0])[0][0])
			button = ImageFillStatusButton(up_image=icon, down_image=icon, hover_image=icon, text=str(resid[1][0]), size=(50,50), opaque=False)
			button.filled = 70
			current_hbox.addChild(button)
			if index % (vbox.width/self.__class__.icon_width) == 0 and  index is not 0:
				vbox.addChild(current_hbox)
				current_hbox = pychan.widgets.HBox()
				current_hbox._setOpaque(False)
		vbox.addChild(current_hbox)
		self.addChild(vbox)
		self.stylize('menu')

class ImageFillStatusButton(pychan.widgets.Container):

	def __init__(self, up_image, down_image, hover_image, text, **kwargs):
		super(ImageFillStatusButton, self).__init__(**kwargs)
		self.up_image, self.down_image, self.hover_image, self.text = up_image, down_image, hover_image, text
		self._filled = 0
		#self._setOpaque(True)
		#self.stylize('default')

	def _set_filled(self, percent):
		""""@var percent: int percent that fillstatus will be green"""
		self._filled = percent
		self._draw()

	def _get_filled(self):
		return self._filled

	filled = property(_get_filled, _set_filled)

	def _draw(self):
		print 'filling'
		button = pychan.widgets.ImageButton(text=self.text, up_image=self.up_image, down_image=self.down_image, hover_image=self.hover_image, size=(50,50))
		self.addChild(button)
		bar1 = pychan.widgets.Icon("content/gui/tab_widget/red_line.png")
		bar2 = pychan.widgets.Icon("content/gui/tab_widget/green_line.png")
		center = (button.width-5, button.height-int(button.height/100.0*self._filled))
		bar1.position = (button.width-5, 0)
		bar2.position = center
		bar2.size = (5, button.height-center[1])
		bar1.size = (5, center[1])
		self.addChild(bar1)
		self.addChild(bar2)