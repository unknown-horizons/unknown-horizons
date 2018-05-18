# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

import functools
import logging

from fife import fife

from horizons.command.uioptions import ClearTradeSlot, SetTradeSlot
from horizons.component.tradepostcomponent import TradePostComponent
from horizons.constants import STORAGE, TRADER
from horizons.extscheduler import ExtScheduler
from horizons.gui.tabs.tabinterface import TabInterface
from horizons.gui.util import create_resource_selection_dialog, get_res_icon_path, load_uh_widget
from horizons.gui.widgets.tradehistoryitem import TradeHistoryItem
from horizons.i18n import gettext as T, gettext_lazy as LazyT
from horizons.util.python.callback import Callback
from horizons.util.worldobject import WorldObject


class BuySellTab(TabInterface):
	"""
	Allows players to tell settlements which resources to buy or sell by adding
	slots in either buy or sell mode and introducing a limit per such slot.
	Also contains the trade history.
	"""
	log = logging.getLogger("gui")

	widget = 'buysellmenu.xml'
	icon_path = 'icons/tabwidget/warehouse/buysell'

	buy_button_path = "content/gui/images/tabwidget/ship_to_warehouse.png"
	sell_button_path = "content/gui/images/tabwidget/warehouse_to_ship.png"

	dummy_icon_path = "icons/resources/none_gray"

	helptext = LazyT('Trade')

	def __init__(self, instance):
		"""Set up the GUI and game logic for the buyselltab."""
		self.inited = False # prevents execution of commands during init
		# this makes sharing code easier
		self.session = instance.session
		self.trade_post = instance.settlement.get_component(TradePostComponent)
		assert isinstance(self.trade_post, TradePostComponent)

		super().__init__()

	def init_widget(self):
		# don't access instance beyond this point, only components

		# add the buy/sell slot widgets
		self.slot_widgets = {}
		self.resources = None # Placeholder for resource gui
		self.add_slots(len(self.trade_post.slots))

		for slot_id in range(len(self.trade_post.slots)):
			if self.trade_post.slots[slot_id] is not None:
				trade_slot_info = self.trade_post.slots[slot_id]
				self.slot_widgets[slot_id].action = 'sell' if trade_slot_info.selling else 'buy'
				self.add_resource(trade_slot_info.resource_id, slot_id, trade_slot_info.limit)

				if trade_slot_info.selling:
					self._show_sell(self.slot_widgets[slot_id])
				else:
					self._show_buy(self.slot_widgets[slot_id])

		# init the trade history
		self.trade_history = self.widget.findChild(name='trade_history')
		self.trade_history_widget_cache = {} # {(tick, player_id, resource_id, amount, gold): widget, ...}

		self.hide()
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
		ExtScheduler().add_new_object(self.refresh, self, run_in=0.4, loops=-1)

	def is_visible(self):
		# this tab sometimes is made up an extra widget, so it must also be considered
		# when checking for visibility
		return super().is_visible() or \
		       (self.resources is not None and self.resources.isVisible())

	def _refresh_trade_history(self):
		self.trade_history.removeAllChildren()
		unused_rows = set(self.trade_history_widget_cache.keys())

		settlement_trade_history = self.trade_post.trade_history
		total_entries = len(settlement_trade_history)
		for i in range(min(4, total_entries)):
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
		if not self.trade_post.buy_list and not self.trade_post.sell_list:
			self._set_hint(T("Click on one of the resource slots to add a trade offer."))

	def add_slots(self, amount):
		"""
		Add `amount` slot widgets to the buysellmenu.
		@param amount: number of slot widgets that are to be added.
		"""
		content = self.widget.findChild(name="content")
		for i in range(amount):
			slot = load_uh_widget('trade_single_slot.xml')
			self.slot_widgets[i] = slot
			slot.id = i
			slot.action = 'buy'
			slot.res = None
			slot.name = "slot_{:d}".format(i)
			slot.findChild(name='button').capture(self.handle_click, event_name='mouseClicked')
			slot.findChild(name='button').path = self.dummy_icon_path
			slider = slot.findChild(name="slider")
			slider.scale_start = 0.0
			slider.scale_end = float(min(self.trade_post.get_inventory().limit, STORAGE.ITEMS_PER_TRADE_SLOT))
			# Set scale according to the settlement inventory size, with a cap
			slot.findChild(name="buysell").capture(Callback(self.toggle_buysell, i))
			fillbar = slot.findChild(name="fillbar")
			# hide fillbar by setting position
			icon = slot.findChild(name="icon")
			fillbar.position = (icon.width - fillbar.width - 1, icon.height)
			content.addChild(slot)
		self.widget.adaptLayout()

	def add_resource(self, resource_id, slot_id, value=None):
		"""
		Adds a resource to the specified slot
		@param resource_id: int - resource id
		@param slot_id: int - slot number of the slot that is to be set
		"""
		self.log.debug("BuySellTab add_resource() resid: %s; slot_id %s; value: %s", resource_id, slot_id, value)

		keep_hint = False
		if self.resources is not None: # Hide resource menu
			self.resources.hide()
			self.show()
			if resource_id != 0: # new res
				self._set_hint(T("Set to buy or sell by clicking on that label, then adjust the amount via the slider to the right."))
			else:
				self._set_hint("")
			keep_hint = True
		slot = self.slot_widgets[slot_id]
		slider = slot.findChild(name="slider")

		if value is None: # use current slider value if player provided no input
			value = int(slider.value)
		else: # set slider to value entered by the player
			slider.value = float(value)

		if slot.action == "sell":
			if slot.res is not None: # slot has been in use before, delete old value
				self.clear_slot(slot_id)
			if resource_id != 0:
				self.set_slot_info(slot.id, resource_id, True, value)
		elif slot.action == "buy":
			if slot.res is not None: # slot has been in use before, delete old value
				self.clear_slot(slot_id)
			if resource_id != 0:
				self.set_slot_info(slot.id, resource_id, False, value)

		button = slot.findChild(name="button")
		fillbar = slot.findChild(name="fillbar")
		# reset slot value for new res
		if resource_id == 0:
			button.path = self.dummy_icon_path
			button.helptext = ""
			slot.findChild(name="amount").text = ""
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
			icon = get_res_icon_path(resource_id)
			icon_disabled = get_res_icon_path(resource_id, greyscale=True)
			button.up_image = icon
			button.down_image = icon
			button.hover_image = icon_disabled
			button.helptext = self.session.db.get_res_name(resource_id)
			slot.res = resource_id
			# use some python magic to assign a res attribute to the slot to
			# save which resource_id it stores
			slider.capture(Callback(self.slider_adjust, resource_id, slot.id))
			slot.findChild(name="amount").text = "{amount:-5d}t".format(amount=value)
			icon = slot.findChild(name="icon")
			inventory = self.trade_post.get_inventory()
			filled = (100 * inventory[resource_id]) // inventory.get_limit(resource_id)
			fillbar.position = (icon.width - fillbar.width - 1,
			                    icon.height - int(icon.height * filled))
			# reuse code from toggle to finish setup (must switch state before, it will reset it)
			slot.action = "sell" if slot.action == "buy" else "buy"
			self.toggle_buysell(slot_id, keep_hint=keep_hint)
		slot.adaptLayout()

	def toggle_buysell(self, slot_id, keep_hint=False):
		"""Switches modes of individual resource slots between 'buy' and 'sell'."""
		slot_widget = self.slot_widgets[slot_id]
		limit = int(slot_widget.findChild(name="slider").value)
		if slot_widget.action == "buy":
			# setting to sell
			self._show_sell(slot_widget)
			slot_widget.action = "sell"
		elif slot_widget.action == "sell":
			# setting to buy
			self._show_buy(slot_widget)
			slot_widget.action = "buy"

		if slot_widget.res is not None:
			selling = slot_widget.action == "sell"
			self.set_slot_info(slot_widget.id, slot_widget.res, selling, limit)

		if not keep_hint:
			self._update_hint(slot_id)

	def set_slot_info(self, slot_id, resource_id, selling, limit):
		assert resource_id is not None
		self.log.debug("BuySellTab: setting slot %d to resource %d, selling=%s, limit %d", slot_id, resource_id, selling, limit)
		self.slot_widgets[slot_id].action = "sell" if selling else "buy"
		if self.inited:
			SetTradeSlot(self.trade_post, slot_id, resource_id, selling, limit).execute(self.session)

	def clear_slot(self, slot_id):
		self.log.debug("BuySellTab: Removing resource in slot %d", slot_id)
		if self.inited:
			ClearTradeSlot(self.trade_post, slot_id).execute(self.session)

	def slider_adjust(self, resource_id, slot_id):
		"""Couples the displayed limit of this slot to the slider position."""
		slider = self.slot_widgets[slot_id].findChild(name="slider")
		limit = int(slider.value)
		self.set_slot_info(slot_id, resource_id, self.slot_widgets[slot_id].action == "sell", limit)
		self.slot_widgets[slot_id].findChild(name="amount").text = "{amount:-5d}t".format(amount=limit)
		self.slot_widgets[slot_id].adaptLayout()
		self._update_hint(slot_id)

	def handle_click(self, widget, event):
		"""Handle clicks on resource slots. Left: change resource; Right: empty slot."""
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
		buy_list = self.trade_post.buy_list
		sell_list = self.trade_post.sell_list

		res_filter = lambda res_id : res_id not in buy_list and res_id not in sell_list
		on_click = functools.partial(self.add_resource, slot_id=slot_id)
		inventory = self.trade_post.get_inventory()

		self.resources = create_resource_selection_dialog(on_click, inventory,
		                                                  self.session.db,
		                                                  res_filter=res_filter)

		self.resources.position = self.widget.position
		self.hide() # hides tab that invoked the selection widget
		self.session.ingame_gui.minimap_to_front()

		self.resources.show() # show selection widget, still display old tab icons

	def _update_hint(self, slot_id):
		"""Sets default hint for last updated slot"""
		slot_widget = self.slot_widgets[slot_id]
		limit = int(slot_widget.findChild(name="slider").value)
		action = slot_widget.action
		price = self.session.db.get_res_value(slot_widget.res)
		if action == "buy":
			hint = T("Will buy {resource_name} for {price} gold/t whenever less than {limit}t are in stock.")
			price *= TRADER.PRICE_MODIFIER_SELL
		elif action == "sell":
			hint = T("Will sell {resource_name} for {price} gold/t whenever more than {limit}t are available.")
			price *= TRADER.PRICE_MODIFIER_BUY

		hint = hint.format(limit=str(limit),
		                   resource_name=self.session.db.get_res_name(slot_widget.res),
		                   price=int(price))
		# same price rounding as in tradepostcomponent
		self._set_hint(hint)

	def _set_hint(self, text):
		lbl = self.widget.findChild(name="hint_label")
		lbl.text = text
		lbl.adaptLayout()

	def _show_buy(self, slot):
		"""Make slot show buy button. Purely visual change"""
		button = slot.findChild(name="buysell")
		button.up_image = self.buy_button_path
		button.helptext = T("Buying")

	def _show_sell(self, slot):
		"""Make slot show sell button. Purely visual change"""
		button = slot.findChild(name="buysell")
		button.up_image = self.sell_button_path
		button.helptext = T("Selling")
