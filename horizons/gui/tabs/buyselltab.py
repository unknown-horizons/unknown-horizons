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
import logging
import functools

from horizons.gui.tabs.tabinterface import TabInterface
from horizons.extscheduler import ExtScheduler
from horizons.command.uioptions import AddToBuyList, AddToSellList, RemoveFromBuyList, \
                                       RemoveFromSellList
from horizons.gui.widgets.tradehistoryitem import TradeHistoryItem
from horizons.util import Callback, WorldObject
from horizons.gui.util import load_uh_widget, get_res_icon_path, create_resource_selection_dialog
from horizons.component.tradepostcomponent import TradePostComponent
from horizons.constants import TRADER

class BuySellTab(TabInterface):
	"""
	Allows players to tell settlements which resources to buy or sell by adding
	slots in either buy or sell mode and introducing a limit per such slot.
	Also contains the trade history.
	"""
	log = logging.getLogger("gui")

	buy_button_path =  "content/gui/images/tabwidget/ship_to_warehouse.png"
	buy_hover_button_path =  "content/gui/images/tabwidget/buysell_toggle.png"
	sell_button_path = "content/gui/images/tabwidget/warehouse_to_ship.png"
	sell_hover_button_path = "content/gui/images/tabwidget/buysell_toggle.png"

	dummy_icon_path = "content/gui/icons/resources/none_gray.png"

	def __init__(self, instance, slots=3, widget='buysellmenu.xml',
	             icon_path='content/gui/icons/tabwidget/warehouse/buysell_%s.png'):
		"""
		Sets up the GUI and game logic for the buyselltab.
		"""
		super(BuySellTab, self).__init__(widget=widget, icon_path=icon_path)
		self.inited = False # prevents execution of commands during init
		# this makes sharing code easier
		self.session = instance.session
		self.tradepost = instance.settlement.get_component(TradePostComponent)
		assert isinstance(self.tradepost, TradePostComponent)
		# don't access instance beyond this point, only components
		self.init_values()

		# add the buy/sell slots
		self.slots = {}
		self.resources = None # Placeholder for resource gui
		self.add_slots(slots)
		slot_count = 0
		# use dynamic change code to init the slots
		buy_list = self.tradepost.buy_list
		for res in buy_list:
			if slot_count < slots:
				self.slots[slot_count].action = 'buy'
				self.add_resource(res, slot_count, buy_list[res])
				self._show_buy( self.slots[slot_count] )

				slot_count += 1
		sell_list = self.tradepost.sell_list
		for res in sell_list:
			if slot_count < slots:
				self.slots[slot_count].action = 'sell'
				self.add_resource(res, slot_count, sell_list[res])
				self._show_sell( self.slots[slot_count] )

				slot_count += 1

		# init the trade history
		self.trade_history = self.widget.findChild(name='trade_history')
		self.trade_history_widget_cache = {} # {(tick, player_id, resource_id, amount, gold): widget, ...}

		self.hide()
		self.helptext = _("Trade")
		self.inited = True

	def hide(self):
		"""Hide the tab and all widgets we may have added at runtime."""
		ExtScheduler().rem_all_classinst_calls(self)
		self.widget.hide()
		if self.resources is not None:
			self.resources.hide()

	def show(self):
		"""Display the tab's content, start the refresher."""
		self.widget.show()
		self.session.ingame_gui.minimap_to_front()
		self.refresh()
		ExtScheduler().add_new_object(self.refresh, self, run_in=0.4, loops = -1)

	def is_visible(self):
		# this tab sometimes is made up an extra widget, so it must also be considered
		# when checking for visibility
		return super(BuySellTab, self).is_visible() or \
		       (self.resources is not None and self.resources.isVisible())

	def _refresh_trade_history(self):
		self.trade_history.removeAllChildren()
		unused_rows = set(self.trade_history_widget_cache.keys())

		settlement_trade_history = self.tradepost.trade_history
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
		buy_list = self.tradepost.buy_list
		sell_list = self.tradepost.sell_list
		if not buy_list and not sell_list:
			self._set_hint( _("Click on one of the resource slots to add a trade offer.") )

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
			slider.scale_end = float(self.tradepost.get_inventory().limit)
			# Set scale according to the settlement inventory size
			slot.findChild(name="buysell").capture(Callback(self.toggle_buysell, num))
			fillbar = slot.findChild(name="fillbar")
			# hide fillbar by setting position
			icon = slot.findChild(name="icon")
			fillbar.position = (icon.width - fillbar.width - 1, icon.height)
			content.addChild(slot)
		self.widget.adaptLayout()


	def add_resource(self, res_id, slot_id, value=None):
		"""
		Adds a resource to the specified slot
		@param res_id: int - resource id
		@param slot: int - slot number of the slot that is to be set
		"""
		self.log.debug("BuySellTab add_resource() resid: %s; slot_id %s; value: %s",
		                                          res_id,    slot_id,    value)

		keep_hint = False
		if self.resources is not None: # Hide resource menu
			self.resources.hide()
			self.show()
			if res_id != 0: # new res
				self._set_hint( _("Set to buy or sell by clicking on that label, then adjust the amount via the slider to the right.") )
			else:
				self._set_hint( u"" )
			keep_hint = True
		slot = self.slots[slot_id]
		slider = slot.findChild(name="slider")

		if value is None: # use current slider value if player provided no input
			value = int(slider.value)
		else: # set slider to value entered by the player
			slider.value = float(value)

		if slot.action is "sell":
			if slot.res is not None: # slot has been in use before, delete old value
				self.remove_sell_from_settlement(slot.res)
			if res_id != 0:
				self.add_sell_to_settlement(res_id, value, slot.id)
		elif slot.action is "buy":
			if slot.res is not None: # slot has been in use before, delete old value
				self.remove_buy_from_settlement(slot.res)
			if res_id != 0:
				self.add_buy_to_settlement(res_id, value, slot.id)
		else:
			assert False

		button = slot.findChild(name="button")
		fillbar = slot.findChild(name="fillbar")
		# reset slot value for new res
		if res_id == 0:
			button.up_image, button.down_image, button.hover_image = [ self.dummy_icon_path ] * 3
			button.helptext = u""
			slot.findChild(name="amount").text = u""
			slot.findChild(name="slider").value = 0.0
			slot.res = None
			slider.capture(None)
			# hide fillbar by setting position
			icon = slot.findChild(name="icon")
			fillbar.position = (icon.width - fillbar.width - 1, icon.height)
			button = slot.findChild(name="buysell")
			button.up_image = None
			button.hover_image = None
		else:
			icon = get_res_icon_path(res_id)
			icon_disabled = get_res_icon_path(res_id, greyscale=True)
			button.up_image = icon
			button.down_image = icon
			button.hover_image = icon_disabled
			button.helptext = self.session.db.get_res_name(res_id)
			slot.res = res_id
			# use some python magic to assign a res attribute to the slot to
			# save which res_id it stores
			slider.capture(Callback(self.slider_adjust, res_id, slot.id))
			slot.findChild(name="amount").text = u"{amount:-5d}t".format(amount=value)
			icon = slot.findChild(name="icon")
			inventory = self.tradepost.get_inventory()
			filled = (100 * inventory[res_id]) // inventory.get_limit(res_id)
			fillbar.position = (icon.width - fillbar.width - 1,
			                    icon.height - int(icon.height*filled))
			# reuse code from toggle to finish setup (must switch state before, it will reset it)
			slot.action = "sell" if slot.action is "buy" else "buy"
			self.toggle_buysell(slot_id, keep_hint=keep_hint)
		slot.adaptLayout()

	def toggle_buysell(self, slot_id, keep_hint=False):
		"""
		Switches modes of individual resource slots between 'buy' and 'sell'.
		"""
		slot = self.slots[slot_id]
		limit = int(slot.findChild(name="slider").value)
		if slot.action is "buy":
			# setting to sell
			self._show_sell(slot)
			slot.action = "sell"
			if slot.res is not None:
				self.remove_buy_from_settlement(slot.res)
				self.add_sell_to_settlement(slot.res, limit, slot.id)
		elif slot.action is "sell":
			# setting to buy
			self._show_buy(slot)
			slot.action = "buy"
			if slot.res is not None:
				self.remove_sell_from_settlement(slot.res)
				self.add_buy_to_settlement(slot.res, limit, slot.id)
		else:
			assert False

		if not keep_hint:
			self._update_hint(slot_id)


	def add_buy_to_settlement(self, res_id, limit, slot):
		"""
		Adds a buy action to this settlement's buy_list.
		Actions have the form (res_id , limit) where limit is the amount until
		which the settlement will try to buy this resource.
		"""
		assert res_id is not None, "Resource to buy is None"
		self.log.debug("BuySellTab: buying of res %s up to %s", res_id, limit)
		self.slots[slot].action = "buy"
		if self.inited:
			AddToBuyList(self.tradepost, res_id, limit).execute(self.session)

	def add_sell_to_settlement(self, res_id, limit, slot):
		"""
		Adds a sell action to this settlement's sell_list.
		Actions have the form (res_id , limit) where limit is the amount until
		which the settlement will allow to sell this resource.
		"""
		assert res_id is not None, "Resource to sell is None"
		self.log.debug("BuySellTab: selling of res %s up to %s", res_id, limit)
		self.slots[slot].action = "sell"
		if self.inited:
			AddToSellList(self.tradepost, res_id, limit).execute(self.session)

	def remove_buy_from_settlement(self, res_id):
		"""Apply removal of buy order. Less powerful than add_*"""
		self.log.debug("BuySellTab: Removing res %s from buy list", res_id)
		if self.inited:
			RemoveFromBuyList(self.tradepost, res_id).execute(self.session)

	def remove_sell_from_settlement(self, res_id):
		"""Apply removal of sell order. Less powerful than add_*"""
		self.log.debug("BuySellTab: Removing res %s from sell list", res_id)
		if self.inited:
			RemoveFromSellList(self.tradepost, res_id).execute(self.session)

	def slider_adjust(self, res_id, slot_id):
		"""
		Couples the displayed limit of this slot to the slider position.
		"""
		slider = self.slots[slot_id].findChild(name="slider")
		limit = int(slider.value)
		action = self.slots[slot_id].action
		if action == "buy":
			self.add_buy_to_settlement(res_id, limit, slot_id)
		elif action == "sell":
			self.add_sell_to_settlement(res_id, limit, slot_id)
		self.slots[slot_id].findChild(name="amount").text = u"{amount:-5d}t".format(amount=limit)
		self.slots[slot_id].adaptLayout()
		self._update_hint(slot_id)

	def handle_click(self, widget, event):
		"""Clicks on resource slots. Left: change resource; Right: empty slot."""
		if event.getButton() == fife.MouseEvent.LEFT:
			self.show_resource_menu(widget.parent.id)
			self.session.ingame_gui.minimap_to_front()
		elif event.getButton() == fife.MouseEvent.RIGHT:
			# remove the buy/sell offer
			self.add_resource(0, widget.parent.id)

	def show_resource_menu(self, slot_id):
		"""
		Displays a menu where players can choose which resource to add in the
		selected slot. Available resources are all possible resources and a
		'None' resource which allows to delete slot actions.
		The resources are ordered by their res_id.
		"""
		# create dlg
		buy_list = self.tradepost.buy_list
		sell_list = self.tradepost.sell_list

		res_filter = lambda res_id : res_id not in buy_list and res_id not in sell_list
		on_click = functools.partial(self.add_resource, slot_id=slot_id)
		inventory = self.tradepost.get_inventory()

		self.resources = create_resource_selection_dialog(on_click, inventory,
		                                                  self.session.db,
		                                                  res_filter=res_filter)

		self.resources.position = self.widget.position
		self.hide() # hides tab that invoked the selection widget
		self.session.ingame_gui.minimap_to_front()

		self.resources.show() # show selection widget, still display old tab icons


	def _update_hint(self, slot_id):
		"""Sets default hint for last updated slot"""
		slot = self.slots[slot_id]
		limit = int( slot.findChild(name="slider").value )
		action = slot.action
		price = self.session.db.get_res_value(slot.res)
		if action == "buy":
			#xgettext:python-format
			hint = _("Will buy {resource_name} for {price} gold/t whenever less than {limit}t are in stock.")
			price *= TRADER.PRICE_MODIFIER_SELL
		elif action == "sell":
			#xgettext:python-format
			hint = _("Will sell {resource_name} for {price} gold/t whenever more than {limit}t are available.")
			price *= TRADER.PRICE_MODIFIER_BUY

		hint = hint.format(limit=unicode(limit),
		                   resource_name=self.session.db.get_res_name(slot.res),
		                   price=int(price))
		# same price rounding as in tradepostcomponent
		self._set_hint( hint )

	def _set_hint(self, text):
		lbl = self.widget.findChild(name="hint_label")
		lbl.text = text
		lbl.adaptLayout()

	def _show_buy(self, slot):
		"""Make slot show buy button. Purely visual change"""
		button = slot.findChild(name="buysell")
		button.up_image = self.buy_button_path
		button.hover_image = self.buy_hover_button_path
		button.helptext = _("Buying")

	def _show_sell(self, slot):
		"""Make slot show sell button. Purely visual change"""
		button = slot.findChild(name="buysell")
		button.up_image = self.sell_button_path
		button.hover_image = self.sell_hover_button_path
		button.helptext = _("Selling")
