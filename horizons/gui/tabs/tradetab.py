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

import logging

from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton
from horizons.gui.tabs.tabinterface import TabInterface
from horizons.command.uioptions import SellResource, BuyResource, TransferResource
from horizons.util import Callback
from horizons.component.tradepostcomponent import TradePostComponent
from horizons.component.storagecomponent import StorageComponent
from horizons.component.namedcomponent import NamedComponent


class TradeTab(TabInterface):
	"""Ship to tradepost trade tab. International as well as national trade."""
	log = logging.getLogger("gui.tabs.tradetab")

	scheduled_update_delay = 0.3

	# map the size buttons in the gui to an amount
	exchange_size_buttons = {
	  1 : 'size_1',
	  5 : 'size_2',
	  10: 'size_3',
	  20: 'size_4',
	  50: 'size_5',
	}

	images = {
	  'box_highlighted': 'content/gui/icons/ship/smallbutton_a.png',
	  'box': 'content/gui/icons/ship/smallbutton.png',
	}

	def __init__(self, instance):
		"""
		@param instance: ship instance used for trading
		"""
		super(TradeTab,self).__init__(widget='tradetab.xml',
		                              icon_path='content/gui/icons/tabwidget/warehouse/buysell_%s.png')
		events = {}
		for k, v in self.exchange_size_buttons.iteritems():
			events[v] = Callback(self.set_exchange, k)
		self.widget.mapEvents(events)
		self.instance = instance
		self.partner = None
		self.set_exchange(50, initial=True)

	def refresh(self):
		super(TradeTab, self).refresh()
		self.draw_widget()

	def draw_widget(self):
		self.widget.findChild(name='ship_name').text = self.instance.get_component(NamedComponent).name
		self.partners = self.instance.get_tradeable_warehouses()
		# set up gui dynamically according to partners
		# NOTE: init on inventories will be optimised away internally if it's only an update
		if self.partners:
			partner_label = self.widget.findChild(name='partners')
			nearest_partner = self.get_nearest_partner(self.partners)
			partner_label.text = self.partners[nearest_partner].settlement.get_component(NamedComponent).name

			new_partner = self.partners[nearest_partner]
			different_partner = new_partner is not self.partner
			if self.partner is not None and different_partner:
				self.__remove_changelisteners()
			self.partner = new_partner
			if different_partner:
				self.__add_changelisteners()

			is_own = self.partner.owner is self.instance.owner
			if not is_own: # foreign warehouse => disable exchange widget, enable trade interface
				self.widget.findChild(name='domestic').hide()
				selling_inventory = self.widget.findChild(name='selling_inventory')
				selling_inventory.init(self.instance.session.db,
				                       self.partner.get_component(StorageComponent).inventory,
				                       self.partner.settlement.get_component(TradePostComponent).sell_list,
				                       selling=True)
				for button in self.get_widgets_by_class(selling_inventory, ImageFillStatusButton):
					button.button.capture(Callback(self.transfer, button.res_id, self.partner.settlement, True))

				buying_inventory = self.widget.findChild(name='buying_inventory')
				buying_inventory.init(self.instance.session.db,
				                      self.partner.get_component(StorageComponent).inventory,
				                      self.partner.settlement.get_component(TradePostComponent).buy_list,
				                      selling=False)
				for button in self.get_widgets_by_class(buying_inventory, ImageFillStatusButton):
					button.button.capture(Callback(self.transfer, button.res_id, self.partner.settlement, False))
				self.widget.findChild(name='international').show()
			else: # own warehouse => enable exchange widget, disable trade interface
				self.widget.findChild(name='international').hide()
				inv_partner = self.widget.findChild(name='inventory_partner') # This is no BuySellInventory!
				inv_partner.init(self.instance.session.db,
				                 self.partner.get_component(StorageComponent).inventory)
				for button in self.get_widgets_by_class(inv_partner, ImageFillStatusButton):
					button.button.capture(Callback(self.transfer, button.res_id, self.partner.settlement, self.instance))
				self.widget.findChild(name='domestic').show()

			inv = self.widget.findChild(name='inventory_ship')
			inv.init(self.instance.session.db, self.instance.get_component(StorageComponent).inventory)
			for button in self.get_widgets_by_class(inv, ImageFillStatusButton):
				button.button.capture(Callback(self.transfer, button.res_id, self.partner.settlement, False))
			self.widget.adaptLayout()
		else:
			# no partner in range any more
			pass

	def __remove_changelisteners(self):
		# never redraw on clicks immediately because of
		# http://fife.trac.cvsdude.com/engine/ticket/387
		# This way, there is a chance of clicks being noticed by pychan.
		# The cost is to delay all updates, which in this case is 0.3 sec, therefore deemed bearable.

		# need to be idempotent, show/hide calls it in arbitrary order
		if self.instance:
			self.instance.discard_change_listener(self._schedule_refresh)
			self.instance.get_component(StorageComponent).inventory.discard_change_listener(self._schedule_refresh)
		if self.partner:
			self.partner.get_component(StorageComponent).inventory.discard_change_listener(self._schedule_refresh)
			self.partner.settlement.get_component(TradePostComponent).discard_change_listener(self._schedule_refresh)

	def __add_changelisteners(self):
		# need to be idempotent, show/hide calls it in arbitrary order
		if self.instance:
			self.instance.add_change_listener(self._schedule_refresh, no_duplicates=True)
			self.instance.get_component(StorageComponent).inventory.add_change_listener(self._schedule_refresh, no_duplicates=True)
		if self.partner:
			self.partner.get_component(StorageComponent).inventory.add_change_listener(self._schedule_refresh, no_duplicates=True)
			self.partner.settlement.get_component(TradePostComponent).add_change_listener(self._schedule_refresh, no_duplicates=True)

	def hide(self):
		self.widget.hide()
		self.__remove_changelisteners()

	def show(self):
		self.widget.show()
		self.__add_changelisteners()
		self.refresh()

	def set_exchange(self, size, initial=False):
		"""
		Highlight radio button with selected amount and deselect old highlighted.
		@param initial: bool, use it to set exchange size when initing the widget
		"""
		if not initial:
			old_box = self.widget.findChild(name= self.exchange_size_buttons[self.exchange])
			old_box.up_image = self.images['box']

		box_h = self.widget.findChild(name= self.exchange_size_buttons[size])
		box_h.up_image = self.images['box_highlighted']

		self.exchange = size
		self.log.debug("Tradewidget: exchange size now: %s", size)
		if not initial:
			self.draw_widget()

	def transfer(self, res_id, settlement, selling):
		"""Buy or sell the resources"""
		if self.instance.position.distance(settlement.warehouse.position) <= self.instance.radius:
			is_own = settlement.owner is self.instance.owner
			if selling and not is_own: # ship sells resources to settlement
				self.log.debug('InternationalTrade: %s/%s is selling %d of res %d to %s/%s',
				               self.instance.get_component(NamedComponent).name, self.instance.owner.name,
				               self.exchange, res_id,
				               settlement.get_component(NamedComponent).name, settlement.owner.name)
				# international trading has own error handling, no signal_error
				SellResource(settlement.get_component(TradePostComponent), self.instance,
				             res_id, self.exchange).execute(self.instance.session)
			elif selling and is_own: # transfer from settlement to ship
				self.log.debug('Trade: Transferring %s of res %s from %s/%s to %s/%s',
				               self.exchange, res_id,
				               settlement.get_component(NamedComponent).name, settlement.owner.name,
				               self.instance.get_component(NamedComponent).name, self.instance.owner.name)
				TransferResource(self.exchange, res_id, settlement,
				                 self.instance, signal_errors=True).execute(self.instance.session)

			elif not selling and not is_own: # ship buys resources from settlement
				self.log.debug('InternationalTrade: %s/%s is buying %d of res %d from %s/%s',
				               self.instance.get_component(NamedComponent).name,
				               self.instance.owner.name, self.exchange, res_id,
				               settlement.get_component(NamedComponent).name, settlement.owner.name)
				# international trading has own error handling, no signal_error
				BuyResource(settlement.get_component(TradePostComponent), self.instance, res_id, self.exchange).execute(self.instance.session)
			elif not selling and is_own: # transfer from ship to settlement
				self.log.debug('Trade: Transferring %s of res %s from %s/%s to %s/%s',
				               self.exchange, res_id,
				               self.instance.get_component(NamedComponent).name, self.instance.owner.name,
				               settlement.get_component(NamedComponent).name, settlement.owner.name)
				TransferResource(self.exchange, res_id, self.instance,
				                 settlement, signal_errors=True).execute(self.instance.session)
			# let gui update be handled by changelisteners (mp-safe)

	def get_widgets_by_class(self, parent_widget, widget_class):
		"""Gets all widget of a certain widget class from the tab. (e.g. pychan.widgets.Label for all labels)"""
		children = []
		def _find_widget(widget):
			if isinstance(widget, widget_class):
				children.append(widget)
		parent_widget.deepApply(_find_widget)
		return children

	def get_nearest_partner(self, partners):
		nearest = None
		nearest_dist = None
		for partner in partners:
			dist = partner.position.distance(self.instance.position)
			if dist < nearest_dist or nearest_dist is None:
				nearest_dist = dist
				nearest = partners.index(partner)
		return nearest
