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

from fife.extensions import pychan
import logging

import horizons.main

from horizons.i18n import load_xml_translated
from tabinterface import TabInterface

class BuySellTab(TabInterface):

	log = logging.getLogger("gui")

	buy_button_path =  "content/gui/images/icons/hud/main/buysell_buy.png"
	sell_button_path = "content/gui/images/icons/hud/main/buysell_sell.png"

	dummy_icon_path = "content/gui/images/icons/hud/build/dummy_btn.png"

	def __init__(self, instance, slots = 3):
		super(BuySellTab, self).__init__(widget = 'buysellmenu/buysellmenu.xml')
		self.settlement = instance.settlement
		self.init_values()
		self.button_up_image = 'content/gui/images/icons/hud/common/buy_sell_res_u.png'
		self.button_active_image = 'content/gui/images/icons/hud/common/buy_sell_res_a.png'
		self.button_down_image = 'content/gui/images/icons/hud/common/buy_sell_res_d.png'
		self.button_hover_image = 'content/gui/images/icons/hud/common/buy_sell_res_h.png'
		self.slots = {}
		self.resources = None # Placeholder for resource gui
		self.add_slots(slots)
		i = 0
		for res in self.settlement.buy_list:
			if i < self.slots:
				self.add_resource(res, i, self.settlement.buy_list[res])
				i += 1
		for res in self.settlement.sell_list:
			if i < self.slots:
				self.add_resource(res, i, self.settlement.sell_list[res])
				self.toggle_buysell(i)
				i += 1
		self.hide()
		self.tooltip = u"Trade"

	def hide(self):
		self.widget.hide()
		if self.resources is not None:
			self.resources.hide()

	def show(self):
		self.widget.show()
		self.settlement.session.ingame_gui.minimap_to_front()

	def refresh(self):
		# We don't need to refresh
		pass

	def add_slots(self, num):
		"""Adds num amount of slots to the buysellmenu.
		@param num: amount of slots that are to be added."""
		content = self.widget.findChild(name="content")
		assert(content is not None)
		for num in range(0, num):
			slot = load_xml_translated('buysellmenu/single_slot.xml')
			self.slots[num] = slot
			slot.id = num
			slot.action = 'buy'
			slot.res = None
			slot.findChild(name='button').capture(pychan.tools.callbackWithArguments(self.show_resource_menu, num))
			slot.findChild(name='amount').stylize('menu_black')
			slider = slot.findChild(name="slider")
			slider.setScaleEnd(float(self.settlement.inventory.limit))# Set scale according to the settlements inventory size
			slot.findChild(name="buysell").capture(pychan.tools.callbackWithArguments(self.toggle_buysell, num))
			fillbar = slot.findChild(name="fillbar")
			# save fillbar for slot, and remove it (workaround cause you can't just show/hide it)
			slot.fillbar = fillbar
			slot.removeChild(fillbar)
			content.addChild(slot)
		self.widget.adaptLayout()


	def add_resource(self, res_id, slot_id, value=None):
		"""Adds a resource to the specified slot
		@param res_id: int - resource id
		@param slot: int - slot number of the slot that is to be set"""
		self.log.debug("BuySellTab add_resource() resid: %s; slot_id %s; value: %s",  \
									 res_id, slot_id, value)

		if self.resources is not None: # Hide resource menu
			self.resources.hide()
			self.show()
		slot = self.slots[slot_id]
		slider = slot.findChild(name="slider")
		if value is None:
			value = int(slider.getValue()) # If no value is provided, take current slider value
		else:
			slider.setValue(float(value)) # set slider correctly

		if slot.action is "sell":
			if slot.res is not None: # slot has been in use before, delete old value
				del self.settlement.sell_list[slot.res]
			if res_id != 0:
				self.add_sell_to_settlement(res_id, value, slot.id)
		else:
			if slot.action is "buy" and slot.res is not None:
				del self.settlement.buy_list[slot.res]
			if res_id != 0:
				self.add_buy_to_settlement(res_id, value, slot.id)

		button = slot.findChild(name="button")
		if hasattr(slot, 'fillbar'):
			slot.addChild(slot.fillbar)
		fillbar = slot.findChild(name="fillbar")
		if res_id == 0:
			button.up_image, button.down_image, button.hover_image = [ self.dummy_icon_path ] * 3
			slot.findChild(name="amount").text = u""
			slot.res = None
			slider.capture(None)
			# remove child, but save it as pychan obj
			slot.fillbar = fillbar
			slot.removeChild(fillbar)
		else:
			icons = horizons.main.db.get_res_icon(res_id)
			button.up_image = icons[0]
			button.down_image = icons[0]
			button.hover_image = icons[1] # disabled icon
			slot.res = res_id # use some python magic to assign a res attribute to the slot to save which res_id he stores
			slider.capture(pychan.tools.callbackWithArguments(self.slider_adjust, res_id, slot.id))
			slot.findChild(name="amount").text = unicode(value)+"t"
			icon = slot.findChild(name="icon")
			inventory = self.settlement.inventory
			filled = float(inventory[res_id]) / inventory.get_limit(res_id)
			fillbar.position = (icon.width - fillbar.width - 1,
			                    icon.height - int(icon.height*filled))
		slot.adaptLayout()

	def toggle_buysell(self, slot):
		slot = self.slots[slot]
		button = slot.findChild(name="buysell")
		limit = int(slot.findChild(name="slider").getValue())
		if slot.action is "buy":
			# setting to sell
			button.up_image = self.sell_button_path
			button.hover_image = self.sell_button_path
			slot.action = "sell"
			if slot.res is not None:
				if slot.res in self.settlement.buy_list:
					self.log.debug("BuySellTab: Removing res %s from buy list", slot.res)
					del self.settlement.buy_list[slot.res]
				self.add_sell_to_settlement(slot.res, limit, slot.id)
		elif slot.action is "sell":
			# setting to buy
			button.up_image = self.buy_button_path
			button.hover_image = self.buy_button_path
			slot.action = "buy"
			if slot.res is not None:
				if slot.res in self.settlement.sell_list:
					self.log.debug("BuySellTab: Removing res %s from sell list", slot.res)
					del self.settlement.sell_list[slot.res]
				self.add_buy_to_settlement(slot.res, limit, slot.id)
		#print "Buylist:", self.settlement.buy_list
		#print "Selllist:", self.settlement.sell_list



	def add_buy_to_settlement(self, res_id, limit, slot):
		#print "limit:", limit
		assert res_id is not None, "Resource to buy is None"
		self.log.debug("BuySellTab: buying of res %s up to %s", res_id, limit)
		self.slots[slot].action = "buy"
		self.settlement.buy_list[res_id] = limit
		#print self.settlement.buy_list


	def add_sell_to_settlement(self, res_id, limit, slot):
		#print "limit:", limit
		assert res_id is not None, "Resource to sell is None"
		self.log.debug("BuySellTab: selling of res %s up to %s", res_id, limit)
		self.slots[slot].action = "sell"
		self.settlement.sell_list[res_id] = limit
		#print self.settlement.sell_list

	def slider_adjust(self, res_id, slot):
		slider = self.slots[slot].findChild(name="slider")
		if self.slots[slot].action is "buy":
			self.add_buy_to_settlement(res_id, int(slider.getValue()), slot)
		elif self.slots[slot].action is "sell":
			self.add_sell_to_settlement(res_id, int(slider.getValue()), slot)
		self.slots[slot].findChild(name="amount").text = unicode(int(slider.getValue()))+'t'
		self.slots[slot].adaptLayout()


	def show_resource_menu(self, slot_id):
		self.resources = load_xml_translated('buysellmenu/resources.xml')
		self.resources.position = self.widget.position
		button_width = 50
		vbox = self.resources.findChild(name="resources")
		current_hbox = pychan.widgets.HBox(padding = 2)
		index = 1
		resources = horizons.main.db.get_res_id_and_icon(True)
		# Add the zero element to the beginning that allows to remove the currently sold/bought resource
		for (res_id, icon) in [(0, self.dummy_icon_path)] + list(resources):
			if res_id in self.settlement.buy_list or res_id in self.settlement.sell_list:
				continue # don't show resources that are already in the list
			button = pychan.widgets.ImageButton(size=(50, 50))
			button.up_image, button.down_image, button.hover_image = icon, icon, icon
			button.capture(pychan.tools.callbackWithArguments(self.add_resource, res_id, slot_id))
			current_hbox.addChild(button)
			if index % (vbox.width/(button_width)) == 0 and index is not 0:
				vbox.addChild(current_hbox)
				current_hbox = pychan.widgets.HBox(padding=0)
			index += 1
		vbox.addChild(current_hbox)
		vbox.adaptLayout()
		self.resources.addChild(vbox)
		self.resources.stylize('headline')
		self.hide()
		self.resources.show()
		self.settlement.session.ingame_gui.minimap_to_front()

