# ###################################################
# Copyright (C) 2008 The Unknown Horizons Team
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
import game.main

from game.util.inventory_widget import ImageFillStatusButton
from game.world.building.storages import BranchOffice

class TradeWidget(object):
	radius = 4 # objects within this radius can be traded with

	def __init__(self, main_instance):
		self.widget = game.main.fife.pychan.loadXML('content/gui/ship/trade.xml')
		self.widget.position = (
			game.main.session.ingame_gui.gui['minimap'].position[1] - game.main.session.ingame_gui.gui['minimap'].size[0] - 30 if game.main.fife.settings.getScreenWidth()/2 + self.widget.size[0]/2 > game.main.session.ingame_gui.gui['minimap'].position[0] else game.main.fife.settings.getScreenWidth()/2 - self.widget.size[0]/2,
			game.main.fife.settings.getScreenHeight() - self.widget.size[1] - 35
		)
		self.widget.stylize('menu')
		self.widget.mapEvents({
				'size_1' : game.main.fife.pychan.tools.callbackWithArguments(self.set_exchange, 1),
				'size_2' : game.main.fife.pychan.tools.callbackWithArguments(self.set_exchange, 5),
				'size_3' : game.main.fife.pychan.tools.callbackWithArguments(self.set_exchange, 10),
				'size_4' : game.main.fife.pychan.tools.callbackWithArguments(self.set_exchange, 20),
				'size_5' : game.main.fife.pychan.tools.callbackWithArguments(self.set_exchange, 50),
		})
		self.main_instance = main_instance
		self.partner = None
		self.exchange = 10
		self.draw_widget()

	def draw_widget(self):
		self.partners = self.find_partner()
		if len(self.partners) > 0:
			dropdown = self.widget.findChild(name='partners')
			#dropdown.setInitialData([item.settlement.name for item in self.partners])
			#dropdown.capture(game.main.fife.pychan.tools.callbackWithArguments(self.set_partner, dropdown.getData()))
			nearest_partner = self.get_nearest_partner(self.partners)
			#dropdown.setData(nearest_partner)
			dropdown.text = self.partners[nearest_partner].settlement.name # label fix for release use only
			self.partner = self.partners[nearest_partner]
			inv_partner = self.widget.findChild(name='inventory_partner')
			inv_partner.inventory = self.partner.inventory
			for button in self.get_widgets_by_class(inv_partner, ImageFillStatusButton):
				button.button.capture(game.main.fife.pychan.tools.callbackWithArguments(self.transfer, button.res_id, self.partner, self.main_instance))
			inv = self.widget.findChild(name='inventory_ship')
			inv.inventory = self.main_instance.inventory
			for button in self.get_widgets_by_class(inv, ImageFillStatusButton):
				button.button.capture(game.main.fife.pychan.tools.callbackWithArguments(self.transfer, button.res_id,self.main_instance, self.partner))
			self.widget._recursiveResizeToContent()


	def set_partner(self, partner_id):
		self.partner = self.partners[partner_id]

	def hide(self):
		self.widget.hide()

	def show(self):
		self.widget.show()

	def set_exchange(self, size):
		self.exchange = size
		#print 'TradeWidget debug: Exchange size now:', self.exchange

	def transfer(self, res_id, transfer_from, transfer_to):
		if self.main_instance.position.distance(transfer_to.position) <= self.radius and \
			 transfer_to is not None and transfer_from is not None:
			#print 'TradeWidget debug: Transfering', self.exchange, 't of resource', res_id, 'from', transfer_from.name, 'to', transfer_to.name
			ret = transfer_from.inventory.alter(res_id, -self.exchange) #take ressources, ret = difference to exchange(might not have hat exchange number of res in store)
			#print 'ret1:', ret
			ret = self.exchange if self.exchange < abs(ret) else abs(ret)
			#print 'ret2:', ret
			ret = transfer_to.inventory.alter(res_id, self.exchange-ret) # give ressources
			#print 'ret3:', ret
			transfer_from.inventory.alter(res_id, ret) #return ressources that did not fit
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
		for island in game.main.session.world.islands:
			for building in island.buildings:
				if isinstance(building, BranchOffice) and building.position.distance(self.main_instance.position) <= self.radius:
					partners.append(building)
		#TODO: Add ships
		return partners

	def get_nearest_partner(self, partners):
		nearest = None
		nearest_dist = None
		for partner in partners:
			dist = partner.position.distance(self.main_instance.position)
			nearest = partners.index(partner) if dist < nearest_dist or nearest_dist is None else nearest
			nearest_dist = dist if dist < nearest_dist or nearest_dist is None else nearest_dist
		return nearest
