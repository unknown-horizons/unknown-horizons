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
import logging

import horizons.main

from horizons.gui.widgets.inventory import ImageFillStatusButton
from horizons.i18n import load_xml_translated

class TradeWidget(object):
	log = logging.getLogger("gui.tradewidget")

	# objects within this radius can be traded with, only used if the
	# main instance does not have a radius attribute
	radius = 5

	# map the size buttons in the gui to an amount
	exchange_size_buttons = {
	  1: 'size_1',
	  5: 'size_2',
	  10: 'size_3',
	  20: 'size_4',
	  50: 'size_5'
	  }

	images = {
	  #'box_highlighted': 'content/gui/images/icons/hud/ship/civil_32_h.png',
	  'box_highlighted': 'content/gui/images/icons/hud/ship/button_small_a.png',
	  'box': 'content/gui/images/icons/hud/ship/button_small.png'
	  }

	def __init__(self, main_instance):
		self.widget = load_xml_translated('ship/trade.xml')
		self.widget.position = (
			horizons.main.fife.settings.getScreenWidth() - self.widget.size[0],
			157
		)
		self.widget.stylize('menu_black')
		self.widget.findChild(name='headline').stylize('headline') # style definition for headline
		events = {}
		for k, v in self.exchange_size_buttons.iteritems():
			events[v] = horizons.main.fife.pychan.tools.callbackWithArguments(self.set_exchange, k)
		self.widget.mapEvents(events)
		self.main_instance = main_instance
		self.partner = None
		self.set_exchange(10, initial=True)
		self.draw_widget()
		if hasattr(self.main_instance, 'radius'):
			self.radius = self.main_instance.radius

	def draw_widget(self):
		self.partners = self.find_partner()
		if len(self.partners) > 0:
			dropdown = self.widget.findChild(name='partners')
			#dropdown.setInitialData([item.settlement.name for item in self.partners])
			#dropdown.capture(horizons.main.fife.pychan.tools.callbackWithArguments(self.set_partner, dropdown.getData()))
			nearest_partner = self.get_nearest_partner(self.partners)
			#dropdown.setData(nearest_partner)
			dropdown.text = unicode(self.partners[nearest_partner].settlement.name) # label fix for release use only
			self.partner = self.partners[nearest_partner]
			inv_partner = self.widget.findChild(name='inventory_partner')
			inv_partner.inventory = self.partner.inventory
			for button in self.get_widgets_by_class(inv_partner, ImageFillStatusButton):
				button.button.capture(horizons.main.fife.pychan.tools.callbackWithArguments(self.transfer, button.res_id, self.partner, self.main_instance))
			inv = self.widget.findChild(name='inventory_ship')
			inv.inventory = self.main_instance.inventory
			for button in self.get_widgets_by_class(inv, ImageFillStatusButton):
				button.button.capture(horizons.main.fife.pychan.tools.callbackWithArguments(self.transfer, button.res_id, self.main_instance, self.partner))
			self.widget.adaptLayout()

	def set_partner(self, partner_id):
		self.partner = self.partners[partner_id]

	def hide(self):
		self.widget.hide()

	def show(self):
		self.widget.show()

	def set_exchange(self, size, initial = False):
		"""
		@param initial: bool, use it to set exchange size when initing the widget
		"""
		# highlight box with selected amount and deselect old highlighted
		if not initial:
			old_box = self.widget.findChild(name= self.exchange_size_buttons[self.exchange])
			old_box.up_image = self.images['box']

		box_h = self.widget.findChild(name= self.exchange_size_buttons[size])
		box_h.up_image = self.images['box_highlighted']

		self.exchange = size
		self.log.debug("Tradewidget: exchange size now: %s", size)
		if not initial:
			self.draw_widget()

	def transfer(self, res_id, transfer_from, transfer_to):
		"""Transfers self.exchange tons of resid from transfer_from to transfer_to"""
		if self.main_instance.position.distance(transfer_to.position) <= self.radius and \
			 transfer_to is not None and transfer_from is not None:
			#print 'TradeWidget debug: Transferring', self.exchange, 't of resource', res_id, 'from', transfer_from.name, 'to', transfer_to.name
			# take res from transfer_from
			ret = transfer_from.inventory.alter(res_id, -self.exchange)
			# check if we were able to get the planed amount
			ret = self.exchange if self.exchange < abs(ret) else abs(ret)
			# put res to transfer_to
			ret = transfer_to.inventory.alter(res_id, self.exchange-ret)
			transfer_from.inventory.alter(res_id, ret) #return resources that did not fit
			# update gui
			self.draw_widget()

	def get_widgets_by_class(self, parent_widget, widget_class):
		"""Gets all widget of a certain widget class from the tab. (e.g. pychan.widgets.Label for all labels)"""
		children = []
		def _find_widget(widget):
			if isinstance(widget, widget_class):
				children.append(widget)
		parent_widget.deepApply(_find_widget)
		return children

	def find_partner(self):
		"""find all partners in radius"""
		partners = []
		branch_offices = horizons.main.session.world.get_branch_offices(position=self.main_instance.position, radius=self.radius)
		if branch_offices is not None:
			partners.extend(branch_offices)
		return partners

	def get_nearest_partner(self, partners):
		nearest = None
		nearest_dist = None
		for partner in partners:
			dist = partner.position.distance(self.main_instance.position)
			nearest = partners.index(partner) if dist < nearest_dist or nearest_dist is None else nearest
			nearest_dist = dist if dist < nearest_dist or nearest_dist is None else nearest_dist
		return nearest
