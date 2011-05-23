# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from horizons.i18n import load_xml_translated
from horizons.util import Callback
from fife.extensions.pychan import widgets
from horizons.gui.widgets.tooltip import TooltipButton

import horizons.main

class RouteConfig(object):
	"""
	Widget that allows configurating a ship's trading route 
	"""
	dummy_icon_path = "content/gui/icons/buildmenu/outdated/dummy_btn.png"
	buy_button_path = "content/gui/images/tabwidget/buysell_buy.png"
	sell_button_path = "content/gui/images/tabwidget/buysell_sell.png"
	MAX_ENTRIES = 6
	MIN_ENTRIES = 2
	def __init__(self, instance):
		self.instance = instance

		offices = instance.session.world.get_branch_offices()
		self.branch_offices = dict([ (bo.settlement.name, bo) for bo in offices ])
		if not hasattr(instance, 'route'):
			instance.create_route()

		self._init_gui()

	def show(self):
		self._gui.show()

	def hide(self):
		self._gui.hide()

	def start_button_set_active(self):
		self._gui.findChild(name='start_route').set_active()
		self._gui.findChild(name='start_route').tooltip = _('Start route')

	def start_button_set_inactive(self):
		self._gui.findChild(name='start_route').set_inactive()
		self._gui.findChild(name='start_route').tooltip = _('Stop route')

	def start_route(self):
		if len(self.widgets) < self.MIN_ENTRIES:
			return
		self.instance.route.enable()
		self.start_button_set_inactive()

	def stop_route(self):
		self.instance.route.disable()
		self.start_button_set_active()

	def toggle_route(self):
		if not self.instance.route.enabled:
			self.start_route()
		else:
			self.stop_route()

	def is_visible(self):
		return self._gui.isVisible()

	def toggle_visibility(self):
		if self.is_visible():
			self.hide()
		else:
			self.show()

	def remove_entry(self, entry):
		if self.resource_menu_shown:
			self.hide_resource_menu()
		enabled = self.instance.route.enabled
		self.instance.route.disable()
		vbox = self._gui.findChild(name="left_vbox")
		self.slots.pop(entry)
		position = self.widgets.index(entry)
		self.widgets.pop(position)
		self.instance.route.waypoints.pop(position)
		vbox.removeChild(entry)
		if enabled:
			self.instance.route.enable()
		if len(self.widgets) < self.MIN_ENTRIES:
			self.stop_route()
		self.hide()
		self.show()

	def move_entry(self, entry, direction):
		"""
		moves an entry up or down
		"""
		position = self.widgets.index(entry)
		if position == len(self.widgets) and direction is 'down' or \
		   position == 0 and direction is 'up':
			return

		if direction is 'up':
			new_pos = position - 1
		elif direction is 'down':
			new_pos = position + 1
		else:
			return

		vbox = self._gui.findChild(name="left_vbox")
		enabled = self.instance.route.enabled
		self.instance.route.disable()

		vbox.removeChildren(self.widgets)
		self.widgets.insert(new_pos,self.widgets.pop(position))
		self.instance.route.move_waypoint(position, direction)
		vbox.addChildren(self.widgets)

		if enabled:
			self.instance.route.enable()
		self.hide()
		self.show()

	def show_load_icon(self, slot):
		button = slot.findChild(name="buysell")
		button.up_image = self.buy_button_path
		button.hover_image = self.buy_button_path
		slot.action = "load"

	def show_unload_icon(self, slot):
		button = slot.findChild(name="buysell")
		button.up_image = self.sell_button_path
		button.hover_image = self.sell_button_path
		slot.action = "unload"

	def toggle_load_unload(self, slot, entry):
		position = self.widgets.index(entry)
		button = slot.findChild(name="buysell")
		res_button = slot.findChild(name="button")
		res = self.resource_for_icon[res_button.up_image.source]

		if res is not 0:
			self.instance.route.waypoints[position]['resource_list'][res] *= -1

		if slot.action is "unload":
			self.show_load_icon(slot)
		else:
			self.show_unload_icon(slot)

	def slider_adjust(self, slot, res_id, entry):
		position = self.widgets.index(entry)
		slider = slot.findChild(name="slider")
		amount = slot.findChild(name="amount")
		value = int(slider.getValue())
		amount.text = unicode(value) + "t"
		if slot.action is "unload":
			value = -value
		self.instance.route.add_to_resource_list(position, res_id, value)
		slot.adaptLayout()

	def add_resource(self, slot, res_id, entry, has_value = False, value=0):
		button = slot.findChild(name="button")
		position = self.widgets.index(entry)
		#remove old resource from waypoints
		res = self.resource_for_icon[button.up_image.source]
		if res is not 0:
			self.instance.route.remove_from_resource_list(position, res)

		icon = self.icon_for_resource[res_id]
		button.up_image, button.down_image, button.hover_image = icon, icon, icon

		#hide the resource menu
		self.hide_resource_menu()

		slider = slot.findChild(name="slider")

		if not has_value:
			value = int(slider.getValue())
			if slot.action is "unload":
				value = -value

		if value < 0:
			self.show_unload_icon(slot)
			slider.setValue(float(-value))
			amount = -value
		elif value > 0:
			self.show_load_icon(slot)
			slider.setValue(float(value))
			amount = value
		else:
			#if the slider value is 0 keep the load/unload persistent
			slider.setValue(0.)
			amount = value

		if res_id != 0:
			slot.findChild(name="amount").text = unicode(amount) + "t"
			slot.adaptLayout()
			self.instance.route.add_to_resource_list(position, res_id, value)
			slider.capture(Callback(self.slider_adjust, slot, res_id, entry))
		else:
			slot.findChild(name="amount").text = unicode("")

	def show_resource_menu(self, slot, entry):

		position = self.widgets.index(entry)
		if self.resource_menu_shown:
			self.hide_resource_menu()
		self.resource_menu_shown = True
		vbox = self._gui.findChild(name="resources")
		label = self._gui.findChild(name="select_res_label")
		label.text = unicode("Select Resources")

		#hardcoded for 5 works better than vbox.width / button_width
		amount_per_line = 5

		current_hbox = widgets.HBox()
		index = 1

		for res_id in self.icon_for_resource:
			if res_id in self.instance.route.waypoints[position]['resource_list'] and\
			   slot.findChild(name='button').up_image.source is not self.icon_for_resource[res_id]:
				continue
			button = TooltipButton(size=(50,50))
			icon = self.icon_for_resource[res_id]
			button.up_image, button.down_image, button.hover_image = icon, icon, icon
			button.capture(Callback(self.add_resource, slot, res_id, entry))
			if res_id != 0:
				button.tooltip = horizons.main.db.get_res_name(res_id)
			current_hbox.addChild(button)
			if index > amount_per_line:
				index -= amount_per_line
				vbox.addChild(current_hbox)
				current_hbox = widgets.HBox()
			index += 1
		vbox.addChild(current_hbox)

		self.hide()
		self.show()

	def hide_resource_menu(self):
		self.resource_menu_shown = False
		self._gui.findChild(name="resources").removeAllChildren()
		self._gui.findChild(name="select_res_label").text = unicode("")

	def add_trade_slots(self, entry, num):
		x_position = 105
		#initialize slots with empty dict
		self.slots[entry] = {}
		for num in range(0,num):
			slot = load_xml_translated('trade_single_slot.xml')
			slot.position = x_position, 0

			slot.action = "load"

			slider = slot.findChild(name="slider")
			slider.setScaleStart(0.0)
			slider.setScaleEnd(float(self.instance.inventory.limit))

			slot.findChild(name="buysell").capture(Callback(self.toggle_load_unload, slot, entry))

			button = slot.findChild(name="button")
			button.capture(Callback(self.show_resource_menu, slot, entry))
			button.up_image = self.dummy_icon_path
			button.down_image = self.dummy_icon_path
			button.hover_image = self.dummy_icon_path

			icon = slot.findChild(name="icon")
			fillbar = slot.findChild(name="fillbar")
			fillbar.position = (icon.width - fillbar.width -1, icon.height)
			x_position += 60

			entry.addChild(slot)
			self.slots[entry][num] = slot

	def add_gui_entry(self, branch_office, resource_list = {}):
		vbox = self._gui.findChild(name="left_vbox")
		entry = load_xml_translated("route_entry.xml")
		self.widgets.append(entry)

		label = entry.findChild(name="bo_name")
		label.text = unicode(branch_office.settlement.name)

		self.add_trade_slots(entry, self.slots_per_entry)

		index = 1
		for res_id in resource_list:
			if index > self.slots_per_entry:
				break
			self.add_resource(self.slots[entry][index - 1],\
			                  res_id, \
			                  entry, \
			                  has_value = True, \
			                  value = resource_list[res_id])
			index += 1

		entry.mapEvents({
		  'delete_bo/mouseClicked' : Callback(self.remove_entry, entry),
		  'move_up/mouseClicked' : Callback(self.move_entry, entry, 'up'),
		  'move_down/mouseClicked' : Callback(self.move_entry, entry, 'down')
		  })
		vbox.addChild(entry)

	def append_bo(self):
		if len(self.widgets) >= self.MAX_ENTRIES:
			return

		selected = self.listbox._getSelectedItem()

		if selected == None:
			return

		self.instance.route.append(self.branch_offices[selected])
		self.add_gui_entry(self.branch_offices[selected])
		if self.resource_menu_shown:
			self.hide_resource_menu()

		self.hide()
		self.show()

	def _init_gui(self):
		"""
		Initial init of gui.
		widgets : list of route entry widgets
		slots : dict with slots for each entry
		"""
		self._gui = load_xml_translated("configure_route.xml")
		self.listbox = self._gui.findChild(name="branch_office_list")
		self.listbox._setItems(list(self.branch_offices))

		self.widgets=[]
		self.slots={}
		self.slots_per_entry = 3

		resources = horizons.main.db.get_res_id_and_icon(True)
		#map an icon for a resource
		#map a resource for an icon
		self.resource_for_icon = {}
		self.icon_for_resource = {}
		for res_id, icon in list(resources) + [(0, self.dummy_icon_path)]:
			self.resource_for_icon[icon] = res_id
			self.icon_for_resource[res_id] = icon

		#don't do any actions if the resource menu is shown
		self.resource_menu_shown = False
		for entry in self.instance.route.waypoints:
			self.add_gui_entry(entry['branch_office'], entry['resource_list'])
		# we want escape key to close the widget, what needs to be fixed here?
		#self._gui.on_escape = self.hide
		self.start_button_set_active()
		if self.instance.route.enabled:
			self.start_button_set_inactive()

		self._gui.mapEvents({
		  'cancelButton' : self.hide,
		  'add_bo/mouseClicked' : self.append_bo,
		  'start_route/mouseClicked' : self.toggle_route
		  })
		self._gui.position_technique = "automatic" # "center:center"

