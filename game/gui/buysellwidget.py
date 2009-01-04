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

import game.main
import pychan
class BuySellWidget(object):

	def __init__(self, slots, settlement):
		self.settlement = settlement
		self.slots = {}
		self.widget = game.main.fife.pychan.loadXML('content/gui/buysellmenu/buysellmenu.xml')
		self.widget.position = (
			game.main.session.ingame_gui.gui['minimap'].position[1] - game.main.session.ingame_gui.gui['minimap'].size[0] - 30 if game.main.fife.settings.getScreenWidth()/2 + self.widget.size[0]/2 > game.main.session.ingame_gui.gui['minimap'].position[0] else game.main.fife.settings.getScreenWidth()/2 - self.widget.size[0]/2,
			game.main.fife.settings.getScreenHeight() - self.widget.size[1] - 35
		)
		self.resources = None # Placeholder for resource gui
		self.add_slots(slots)

	def hide(self):
		self.widget.hide()
		if self.resources is not None:
			self.resources.hide()

	def show(self):
		self.widget.show()

	def add_slots(self, num):
		"""Adds num amount of slots to the buysellmenu.
		@param num: amount of slots that are to be added."""
		content = self.widget.findChild(name="content")
		assert(content is not None)
		for num in range(0,num):
			slot = game.main.fife.pychan.loadXML('content/gui/buysellmenu/single_slot.xml')
			self.slots[num] = slot
			slot.id = num
			slot.action = None
			slot.res = None
			slot.findChild(name='button').capture(game.main.fife.pychan.tools.callbackWithArguments(self.show_ressource_menu, num))
			slider = slot.findChild(name="slider")
			slider.setScaleEnd(float(self.settlement.inventory.limit))# Set scale according to the settlements inventory size
			slot.findChild(name="buysell").capture(game.main.fife.pychan.tools.callbackWithArguments(self.toggle_buysell, num))
			content.addChild(slot)
		self.widget._recursiveResizeToContent()

	def add_ressource(self, res_id, slot):
		"""Adds a ressource to the specified slot
		@param res_id: int - resource id
		@param slot: int - slot number of the slot that is to be set"""
		slot = self.slots[slot]
		if slot.action is "buy":
			del self.settlement.buy_list[slot.res]
		elif slot.action is "sell":
			del self.settlement.sell_list[slot.res]
		self.resources.hide()
		self.show()
		button = slot.findChild(name="button")
		button.up_image, button.down_image, = (game.main.db("SELECT icon FROM resource WHERE rowid=?", res_id)[0]) * 2
		button.hover_image = game.main.db("SELECT icon_disabled FROM resource WHERE rowid=?", res_id)[0][0]
		slot.findChild(name="amount").text = str(self.settlement.inventory.limit/2)+"t"
		slider = slot.findChild(name="slider")
		slider.setValue(float(self.settlement.inventory.limit/2)) # set first value to half inventory size
		slider.capture(game.main.fife.pychan.tools.callbackWithArguments(self.slider_adjust, res_id, slot.id))
		slot.res = res_id # use some python magic to assign a res attribute to the slot to save which res_id he stores
		self.add_buy_to_settlement(res_id, self.settlement.inventory.limit/2, slot.id)
		slot._recursiveResizeToContent()

	def toggle_buysell(self, slot):
		slot = self.slots[slot]
		button = slot.findChild(name="buysell")
		limit = int(slot.findChild(name="slider").getValue())
		if slot.action is "buy":
			button.up_image="content/gui/images/icons/hud/main/buysell_sell.png"
			slot.action="sell"
			if slot.res in self.settlement.buy_list:
				del self.settlement.buy_list[slot.res]
			self.add_sell_to_settlement(slot.res, limit, slot.id)
		elif slot.action is "sell":
			button.up_image="content/gui/images/icons/hud/main/buysell_buy.png"
			slot.action="buy"
			if slot.res in self.settlement.sell_list:
				del self.settlement.sell_list[slot.res]
			self.add_buy_to_settlement(slot.res, limit, slot.id)
		print "Buylist:", self.settlement.buy_list
		print "Selllist:", self.settlement.sell_list



	def add_buy_to_settlement(self, res_id, limit, slot):
		print "limit:", limit
		self.slots[slot].action = "buy"
		self.settlement.buy_list[res_id] = limit
		print self.settlement.buy_list


	def add_sell_to_settlement(self, res_id, limit, slot):
		print "limit:", limit
		self.slots[slot].action = "sell"
		self.settlement.sell_list[res_id] = limit
		print self.settlement.sell_list

	def slider_adjust(self, res_id, slot):
		slider = self.slots[slot].findChild(name="slider")
		print "Ajusting slider to", slider.getValue()
		if self.slots[slot].action is "buy":
			self.add_buy_to_settlement(res_id, int(slider.getValue()), slot)
		elif self.slots[slot].action is "sell":
			self.add_sell_to_settlement(res_id, int(slider.getValue()), slot)
		self.slots[slot].findChild(name="amount").text = str(int(slider.getValue()))+'t'



	def show_ressource_menu(self, slot_id):
		self.resources = game.main.fife.pychan.loadXML('content/gui/buysellmenu/resources.xml')
		self.resources.position = self.widget.position
		button_width = 50
		vbox = pychan.widgets.VBox(padding = 0)
		vbox.width = self.resources.width
		current_hbox = pychan.widgets.HBox(padding = 2)
		index = 1
		for (res_id,icon) in game.main.db("SELECT rowid, icon FROM resource"):
			if res_id == 1:
				continue # don't show coins
			if res_id in self.settlement.buy_list or res_id in self.settlement.sell_list:
				continue # don't show resources that are already in the list
			button = pychan.widgets.ImageButton(size=(50,50))
			button.up_image, button.down_image, button.hover_image = icon, icon, icon
			button.capture(game.main.fife.pychan.tools.callbackWithArguments(self.add_ressource, res_id, slot_id))
			current_hbox.addChild(button)
			if index % (vbox.width/(button_width)) == 0 and index is not 0:
				vbox.addChild(current_hbox)
				current_hbox = pychan.widgets.HBox(padding=0)
			index += 1
		vbox.addChild(current_hbox)
		self.resources.addChild(vbox)
		self.hide()
		self.resources.show()

