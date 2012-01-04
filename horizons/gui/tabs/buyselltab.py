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

from fife import fife
from fife.extensions import pychan
import logging

from tabinterface import TabInterface
from horizons.extscheduler import ExtScheduler
from horizons.command.uioptions import AddToBuyList, AddToSellList, RemoveFromBuyList, \
                                       RemoveFromSellList
from horizons.gui.widgets.tradehistoryitem import TradeHistoryItem
from horizons.gui.widgets.tooltip import TooltipButton
from horizons.util import Callback, WorldObject
from horizons.util.gui import load_uh_widget, get_res_icon
from horizons.world.component.storagecomponent import StorageComponent
from horizons.world.component.tradepostcomponent import TradePostComponent

class BuySellTab(TabInterface):
	"""
	Allows players to tell settlements which resources to buy or sell by adding
	slots in either buy or sell mode and introducing a limit per such slot.
	Also contains the trade history.
	"""
	log = logging.getLogger("gui")

	buy_button_path =  "content/gui/images/tabwidget/buysell_buy.png"
	sell_button_path = "content/gui/images/tabwidget/buysell_sell.png"

	dummy_icon_path = "content/gui/icons/resources/none_gray.png"

	def __init__(self, instance, slots = 3):
		"""
		Sets up the GUI and game logic for the buyselltab.
		"""
		super(BuySellTab, self).__init__(widget = 'buysellmenu.xml')
		self.settlement = instance.settlement
		self.init_values()
		self.icon_path = 'content/gui/icons/tabwidget/warehouse/buysell_%s.png'
		self.button_up_image = self.icon_path % 'u'
		self.button_active_image = self.icon_path % 'a'
		self.button_down_image = self.icon_path % 'd'
		self.button_hover_image = self.icon_path % 'h'

		# add the buy/sell slots
		self.slots = {}
		self.resources = None # Placeholder for resource gui
		self.add_slots(slots)
		slot_count = 0
		buy_list = self.settlement.get_component(TradePostComponent).buy_list
		for res in buy_list:
			if slot_count < self.slots:
				self.add_resource(res, slot_count, buy_list[res], \
				                  dont_use_commands=True)
				slot_count += 1
		sell_list = self.settlement.get_component(TradePostComponent).sell_list
		for res in sell_list:
			if slot_count < self.slots:
				self.add_resource(res, slot_count, sell_list[res], \
				                  dont_use_commands=True)
				self.toggle_buysell(slot_count, dont_use_commands=True)
				slot_count += 1

		# init the trade history
		self.trade_history = self.widget.findChild(name='trade_history')
		self.trade_history_widget_cache = {} # {(tick, player_id, resource_id, amount, gold): widget, ...}

		self.hide()
		self.tooltip = _("Trade")

	def hide(self):
		"""Hide the tab and all widgets we may have added at runtime."""
		ExtScheduler().rem_all_classinst_calls(self)
		self.widget.hide()
		if self.resources is not None:
			self.resources.hide()

	def show(self):
		"""Display the tab's content, start the refresher."""
		self.widget.show()
		self.settlement.session.ingame_gui.minimap_to_front()
		self.refresh()
		ExtScheduler().add_new_object(self.refresh, self, run_in=0.4, loops = -1)

	def _refresh_trade_history(self):
		self.trade_history.removeAllChildren()
		unused_rows = set(self.trade_history_widget_cache.keys())

		settlement_trade_history = self.settlement.get_component(TradePostComponent).trade_history
		total_entries = len(settlement_trade_history)
		for i in xrange(min(4, total_entries)):
			row = settlement_trade_history[total_entries - i - 1]
			player = WorldObject.get_object_by_id(row[1])
			if row not in self.trade_history_widget_cache:
				self.trade_history_widget_cache[row] = TradeHistoryItem(player, row[2], row[3], row[4])
			widget = self.trade_history_widget_cache[row]
			self.trade_history.addChild(widget)
			unused_rows.discard(row)
		self.trade_history.adaptLayout()

		for row in unused_rows:
			del self.trade_history_widget_cache[row]

	def refresh(self):
		self._refresh_trade_history()
		# TODO: We don't refresh. Ticket #970

	def add_slots(self, num):
		"""
		Adds num amount of slots to the buysellmenu.
		@param num: amount of slots that are to be added.
		"""
		content = self.widget.findChild(name="content")
		assert(content is not None)
		for num in range(0, num):
			slot = load_uh_widget('trade_single_slot.xml')
			self.slots[num] = slot
			slot.id = num
			slot.action = 'buy'
			slot.res = None
			slot.findChild(name='button').capture(self.handle_click, event_name = 'mouseClicked')
			slot.findChild(name='button').up_image = self.dummy_icon_path
			slot.findChild(name='button').down_image = self.dummy_icon_path
			slot.findChild(name='button').hover_image = self.dummy_icon_path
			slot.findChild(name='amount').stylize('menu_black')
			slider = slot.findChild(name="slider")
			slider.scale_start = 0.0
			slider.scale_end = float(self.settlement.get_component(StorageComponent).inventory.limit)
			# Set scale according to the settlement inventory size
			slot.findChild(name="buysell").capture(Callback(self.toggle_buysell, num))
			fillbar = slot.findChild(name="fillbar")
			# hide fillbar by setting position
			icon = slot.findChild(name="icon")
			fillbar.position = (icon.width - fillbar.width - 1, icon.height)
			content.addChild(slot)
		self.widget.adaptLayout()


	def add_resource(self, res_id, slot_id, value=None, dont_use_commands=False):
		"""
		Adds a resource to the specified slot
		@param res_id: int - resource id
		@param slot: int - slot number of the slot that is to be set
		"""
		self.log.debug("BuySellTab add_resource() resid: %s; slot_id %s; value: %s", \
		                                          res_id,    slot_id,    value)

		if self.resources is not None: # Hide resource menu
			self.resources.hide()
			self.show()
		slot = self.slots[slot_id]
		slider = slot.findChild(name="slider")
		if value is None: # use current slider value if player provided no input
			value = int(slider.value)
		else: # set slider to value entered by the player
			slider.value = float(value)

		if slot.action is "sell":
			if slot.res is not None: # slot has been in use before, delete old value
				if dont_use_commands: # dont_use_commands is true if called by __init__
					self.settlement.get_component(TradePostComponent).remove_from_sell_list(slot.res)
				else:
					RemoveFromSellList(self.settlement, slot.res).execute(self.settlement.session)
			if res_id != 0:
				self.add_sell_to_settlement(res_id, value, slot.id, dont_use_commands)
		else:
			if slot.action is "buy" and slot.res is not None:
				if dont_use_commands: # dont_use_commands is true if called by __init__
					self.settlement.get_component(TradePostComponent).remove_from_buy_list(slot.res)
				else:
					RemoveFromBuyList(self.settlement, slot.res).execute(self.settlement.session)
			if res_id != 0:
				self.add_buy_to_settlement(res_id, value, slot.id, dont_use_commands)

		button = slot.findChild(name="button")
		fillbar = slot.findChild(name="fillbar")
		if res_id == 0:
			button.up_image, button.down_image, button.hover_image = [ self.dummy_icon_path ] * 3
			button.tooltip = u""
			slot.findChild(name="amount").text = u""
			slot.res = None
			slider.capture(None)
			# hide fillbar by setting position
			icon = slot.findChild(name="icon")
			fillbar.position = (icon.width - fillbar.width - 1, icon.height)
		else:
			icons = get_res_icon(res_id)
			button.up_image = icons[0]
			button.down_image = icons[0]
			button.hover_image = icons[1] # disabled icon
			button.tooltip = self.settlement.session.db.get_res_name(res_id)
			slot.res = res_id
			# use some python magic to assign a res attribute to the slot to
			# save which res_id it stores
			slider.capture(Callback(self.slider_adjust, res_id, slot.id))
			slot.findChild(name="amount").text = unicode(value)+"t"
			icon = slot.findChild(name="icon")
			inventory = self.settlement.get_component(StorageComponent).inventory
			filled = float(inventory[res_id]) / inventory.get_limit(res_id)
			fillbar.position = (icon.width - fillbar.width - 1,
			                    icon.height - int(icon.height*filled))
		slot.adaptLayout()

	def toggle_buysell(self, slot, dont_use_commands=False):
		"""
		Switches modes of individual resource slots between 'buy' and 'sell'.
		"""
		slot = self.slots[slot]
		button = slot.findChild(name="buysell")
		limit = int(slot.findChild(name="slider").value)
		if slot.action is "buy":
			# setting to sell
			button.up_image = self.sell_button_path
			button.hover_image = self.sell_button_path
			slot.action = "sell"
			if slot.res is not None:
				self.log.debug("BuySellTab: Removing res %s from buy list", slot.res)
				if dont_use_commands: # dont_use_commands is true if called by __init__
					self.settlement.get_component(TradePostComponent).remove_from_buy_list(slot.res)
				else:
					RemoveFromBuyList(self.settlement, slot.res).execute(self.settlement.session)
				self.add_sell_to_settlement(slot.res, limit, slot.id, dont_use_commands)
		elif slot.action is "sell":
			# setting to buy
			button.up_image = self.buy_button_path
			button.hover_image = self.buy_button_path
			slot.action = "buy"
			if slot.res is not None:
				self.log.debug("BuySellTab: Removing res %s from sell list", slot.res)
				if dont_use_commands: # dont_use_commands is true if called by __init__
					self.settlement.get_component(TradePostComponent).remove_from_sell_list(slot.res)
				else:
					RemoveFromSellList(self.settlement, slot.res).execute(self.settlement.session)
				self.add_buy_to_settlement(slot.res, limit, slot.id, dont_use_commands)

	def add_buy_to_settlement(self, res_id, limit, slot, dont_use_commands=False):
		"""
		Adds a buy action to this settlement's buy_list.
		Actions have the form (res_id , limit) where limit is the amount until
		which the settlement will try to buy this resource.
		"""
		assert res_id is not None, "Resource to buy is None"
		self.log.debug("BuySellTab: buying of res %s up to %s", res_id, limit)
		self.slots[slot].action = "buy"
		if dont_use_commands: # dont_use_commands is true if called by __init__
			self.settlement.get_component(TradePostComponent).add_to_buy_list(res_id, limit)
		else:
			AddToBuyList(self.settlement, res_id, limit).execute(self.settlement.session)

	def add_sell_to_settlement(self, res_id, limit, slot, dont_use_commands=False):
		"""
		Adds a sell action to this settlement's sell_list.
		Actions have the form (res_id , limit) where limit is the amount until
		which the settlement will allow to sell this resource.
		"""
		assert res_id is not None, "Resource to sell is None"
		self.log.debug("BuySellTab: selling of res %s up to %s", res_id, limit)
		self.slots[slot].action = "sell"
		if dont_use_commands: # dont_use_commands is true if called by __init__
			self.settlement.get_component(TradePostComponent).add_to_sell_list(res_id, limit)
		else:
			AddToSellList(self.settlement, res_id, limit).execute(self.settlement.session)

	def slider_adjust(self, res_id, slot):
		"""
		Couples the displayed limit of this slot to the slider position.
		"""
		slider = self.slots[slot].findChild(name="slider")
		if self.slots[slot].action is "buy":
			self.add_buy_to_settlement(res_id, int(slider.value), slot)
		elif self.slots[slot].action is "sell":
			self.add_sell_to_settlement(res_id, int(slider.value), slot)
		self.slots[slot].findChild(name="amount").text = unicode(int(slider.value))+'t'
		self.slots[slot].adaptLayout()

	def handle_click(self, widget, event):
		if event.getButton() == fife.MouseEvent.LEFT:
			self.show_resource_menu(widget.parent.id)
		elif event.getButton() == fife.MouseEvent.RIGHT:
			# remove the buy/sell offer
			self.add_resource(0, widget.parent.id, None, False)

	def show_resource_menu(self, slot_id):
		"""
		Displays a menu where players can choose which resource to add in the
		selected slot. Available resources are all possible resources and a
		'None' resource which allows to delete slot actions.
		The resources are ordered by their res_id.
		"""
		self.resources = load_uh_widget('select_trade_resource.xml')
		self.resources.position = self.widget.position
		button_width = 50
		vbox = self.resources.findChild(name="resources")
		amount_per_line = vbox.width / button_width
		current_hbox = pychan.widgets.HBox(name="hbox_0")
		index = 1
		resources = self.settlement.session.db.get_res_id_and_icon(True)
		# Add the zero element to the beginning that allows to remove the currently
		# sold/bought resource
		buy_list = self.settlement.get_component(TradePostComponent).buy_list
		sell_list = self.settlement.get_component(TradePostComponent).sell_list
		for (res_id, icon) in [(0, self.dummy_icon_path)] + list(resources):
			if res_id in buy_list or res_id in sell_list:
				continue # don't show resources that are already in the list
			button = TooltipButton( size=(button_width, button_width), \
			                        name="resource_icon_%02d" % res_id )
			button.up_image, button.down_image, button.hover_image = icon, icon, icon
			if res_id == 0:
				button.tooltip = u""
			else:
				button.tooltip = self.settlement.session.db.get_res_name(res_id)
			button.capture(Callback(self.add_resource, res_id, slot_id))
			current_hbox.addChild(button)
			if index % amount_per_line == 0 and index is not 0:
				vbox.addChild(current_hbox)
				current_hbox = pychan.widgets.HBox(name="hbox_%s" % (index / amount_per_line) )
			index += 1
#		current_hbox.addSpacer(pychan.widgets.layout.Spacer) #TODO: proper alignment
		vbox.addChild(current_hbox)
		vbox.adaptLayout()
		self.hide() # hides tab that invoked the selection widget
		self.resources.show() # show selection widget, still display old tab icons
		self.settlement.session.ingame_gui.minimap_to_front()

