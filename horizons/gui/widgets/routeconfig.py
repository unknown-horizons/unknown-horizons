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

import weakref
import functools

from fife import fife

from horizons.gui.util import load_uh_widget
from horizons.util.python.callback import Callback
from horizons.util.shapes import Point
from fife.extensions.pychan import widgets
from horizons.component.storagecomponent import StorageComponent
from horizons.gui.widgets.minimap import Minimap
from horizons.command.uioptions import RouteConfigCommand
from horizons.component.namedcomponent import NamedComponent
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.gui.util import create_resource_selection_dialog
from horizons.gui.widgets.imagebutton import OkButton

import horizons.globals

class RouteConfig(object):
	"""
	Widget that allows configurating a ship's trading route
	"""
	dummy_icon_path = "content/gui/icons/resources/none_gray.png"
	buy_button_path = "content/gui/images/tabwidget/warehouse_to_ship.png"
	sell_button_path = "content/gui/images/tabwidget/ship_to_warehouse.png"
	hover_button_path = "content/gui/images/tabwidget/buysell_toggle.png"
	MAX_ENTRIES = 7
	MIN_ENTRIES = 2
	def __init__(self, instance):
		self.instance = instance

		if not hasattr(instance, 'route'):
			instance.create_route()

		self._init_gui()

	@property
	def session(self):
		session = self.instance.session
		assert isinstance(session, horizons.session.Session)
		return session

	def show(self):
		self.minimap.draw()
		self._gui.show()

		self.instance.add_remove_listener(self.on_instance_removed, no_duplicates=True)
		self.instance.route.add_change_listener(self.on_route_change, no_duplicates=True, call_listener_now=True)

		self.session.ingame_gui.on_switch_main_widget(self)

	def hide(self):
		self.session.ingame_gui.on_switch_main_widget(None)
		self.minimap.disable()
		self._gui.hide()

		self.instance.discard_remove_listener(self.on_instance_removed)
		self.instance.route.discard_remove_listener(self.on_route_change)

		# make sure user knows that it's not enabled (if it appears to be complete)
		if not self.instance.route.enabled and self.instance.route.can_enable():
			self.session.ingame_gui.message_widget.add(point=None, string_id="ROUTE_DISABLED")

	def on_instance_removed(self):
		self.hide()
		self.instance = None

	def on_route_change(self):
		"""Called on changelistener notifications from the route"""
		if self.instance.route.enabled:
			self.start_button_set_inactive()
		else:
			self.start_button_set_active()

	def start_button_set_active(self):
		self._gui.findChild(name='start_route').set_active()
		self._gui.findChild(name='start_route').helptext = _('Start route')

	def start_button_set_inactive(self):
		self._gui.findChild(name='start_route').set_inactive()
		self._gui.findChild(name='start_route').helptext = _('Stop route')

	def start_route(self):
		if not self.instance.route.can_enable():
			self.instance.session.gui.show_popup(_("Need at least two settlements"),
			                                     _("You need at least two different settlements in your route."))
		else:
			self._route_cmd("enable")

	def stop_route(self):
		self._route_cmd("disable")

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
		vbox = self._gui.findChild(name="left_vbox")
		self.slots.pop(entry)
		position = self.widgets.index(entry)
		self._route_cmd("remove_waypoint", position)
		self.widgets.pop(position)
		vbox.removeChild(entry)

		self._check_no_entries_label()

		self._gui.adaptLayout()

	def _check_no_entries_label(self):
		"""Update hint informing about how to add waypoints. Only visible when there are none."""
		name = "no_entries_hint"
		if not self.instance.route.waypoints:
			lbl = widgets.Label(name=name, text=_("Click on a settlement to add a waypoint!"))
			self._gui.findChild(name="left_vbox").addChild( lbl )
		else:
			lbl = self._gui.findChild(name=name)
			if lbl:
				self._gui.findChild(name="left_vbox").removeChild( lbl )

	def move_entry(self, entry, direction):
		"""
		moves an entry up or down
		"""
		position = self.widgets.index(entry)
		if position == len(self.widgets) and direction is 'down' or \
		   position == 0 and direction is 'up':
			AmbientSoundComponent.play_special('error')
			return

		if direction is 'up':
			new_pos = position - 1
		elif direction is 'down':
			new_pos = position + 1
		else:
			return

		vbox = self._gui.findChild(name="left_vbox")

		vbox.removeChildren(self.widgets)
		self.widgets.insert(new_pos, self.widgets.pop(position))
		self._route_cmd("move_waypoint", position, direction)
		vbox.addChildren(self.widgets)


		self._gui.adaptLayout()
		self._resource_selection_area_layout_hack_fix()

	def show_load_icon(self, slot):
		button = slot.findChild(name="buysell")
		button.up_image = self.buy_button_path
		button.hover_image = self.hover_button_path
		button.helptext = _("Loading into ship")
		slot.action = "load"

	def show_unload_icon(self, slot):
		button = slot.findChild(name="buysell")
		button.up_image = self.sell_button_path
		button.hover_image = self.hover_button_path
		button.helptext = _("Unloading from ship")
		slot.action = "unload"

	def toggle_load_unload(self, slot, entry):
		position = self.widgets.index(entry)
		res_button = slot.findChild(name="button")
		res = self.resource_for_icon[res_button.up_image.source]

		if res != 0:
			self._route_cmd("toggle_load_unload", position, res)

		if slot.action is "unload":
			self.show_load_icon(slot)
		else:
			self.show_unload_icon(slot)

	def slider_adjust(self, slot, res_id, entry):
		position = self.widgets.index(entry)
		slider = slot.findChild(name="slider")
		amount_lbl = slot.findChild(name="amount")
		amount = int(slider.value)
		amount_lbl.text = u'{amount}t'.format(amount=amount)
		if slot.action is "unload":
			amount = -amount
		self._route_cmd("add_to_resource_list", position, res_id, amount)
		slot.adaptLayout()

	def add_resource(self, res_id, slot=None, entry=None, has_value=False, value=0):
		button = slot.findChild(name="button")
		position = self.widgets.index(entry)
		#remove old resource from waypoints
		res = self.resource_for_icon[button.up_image.source]
		if res != 0:
			self._route_cmd("remove_from_resource_list", position, res)

		icon = self.icon_for_resource[res_id]
		button.up_image, button.down_image, button.hover_image = icon, icon, icon
		button.max_size = button.min_size = button.size = (32, 32)

		#hide the resource menu
		self.hide_resource_menu()

		slider = slot.findChild(name="slider")

		if not has_value:
			value = int(slider.value)
			if slot.action is "unload":
				value = -value

		if value < 0:
			self.show_unload_icon(slot)
			slider.value = float(-value)
			amount = -value
		elif value > 0:
			self.show_load_icon(slot)
			slider.value = float(value)
			amount = value
		else:
			#if the slider value is 0 keep the load/unload persistent
			slider.value = 0.
			amount = value

		if res_id != 0:
			slot.findChild(name="amount").text = unicode(amount) + "t"
			slot.adaptLayout()
			self._route_cmd("add_to_resource_list", position, res_id, value)
			slider.capture(Callback(self.slider_adjust, slot, res_id, entry))
		else:
			slot.findChild(name="amount").text = u""

	def handle_resource_click(self, widget, event):
		if event.getButton() == fife.MouseEvent.LEFT:
			self.show_resource_menu(widget.parent, widget.parent.parent)
		elif event.getButton() == fife.MouseEvent.RIGHT:
			# remove the load/unload order
			self.add_resource(slot=widget.parent, res_id=0, entry=widget.parent.parent)

	def show_resource_menu(self, slot, entry):
		position = self.widgets.index(entry)
		if self.resource_menu_shown:
			self.hide_resource_menu()
		self.resource_menu_shown = True

		on_click = functools.partial(self.add_resource, slot=slot, entry=entry)
		settlement = entry.settlement()
		inventory = settlement.get_component(StorageComponent).inventory if settlement else None
		widget = 'traderoute_resource_selection.xml'

		def res_filter(res_id):
			same_icon = slot.findChild(name='button').up_image.source == self.icon_for_resource[res_id]
			already_listed = res_id in self.instance.route.waypoints[position]['resource_list']
			return not (same_icon or already_listed)

		dlg = create_resource_selection_dialog(on_click=on_click, inventory=inventory,
			db=self.session.db, widget=widget, amount_per_line=6, res_filter=res_filter)

		self._gui.findChild(name="traderoute_resources").addChild(dlg)
		self._gui.adaptLayout()
		self._resource_selection_area_layout_hack_fix()

	def _resource_selection_area_layout_hack_fix(self):
		# no one knows why this is necessary, but sometimes we need to set the values anew
		vbox = self._gui.findChild(name="traderoute_resources")
		scrollarea = vbox.findChild(name="resources_scrollarea")
		if scrollarea:
			scrollarea.max_width = scrollarea.width = vbox.max_width = vbox.width = 320

	def hide_resource_menu(self):
		self.resource_menu_shown = False
		self._gui.findChild(name="traderoute_resources").removeAllChildren()

	def add_trade_slots(self, entry, slot_amount):
		x_position = 105
		#initialize slots with empty dict
		self.slots[entry] = {}
		for num in range(slot_amount):
			slot = load_uh_widget('trade_single_slot.xml')
			slot.position = (x_position, 0)

			slot.action = "load"

			slider = slot.findChild(name="slider")
			slider.scale_start = 0.0
			slider.scale_end = float(self.instance.get_component(StorageComponent).inventory.limit)

			slot.findChild(name="buysell").capture(Callback(self.toggle_load_unload, slot, entry))

			button = slot.findChild(name="button")
			button.capture(self.handle_resource_click, event_name='mouseClicked')
			button.up_image = self.dummy_icon_path
			button.down_image = self.dummy_icon_path
			button.hover_image = self.dummy_icon_path

			icon = slot.findChild(name="icon")
			fillbar = slot.findChild(name="fillbar")
			fillbar.position = (icon.width - fillbar.width -1, icon.height)
			x_position += 60

			entry.addChild(slot)
			self.slots[entry][num] = slot
			self.show_load_icon(slot)

	def add_gui_entry(self, warehouse, resource_list=None):
		vbox = self._gui.findChild(name="left_vbox")
		entry = load_uh_widget("route_entry.xml")
		entry.settlement = weakref.ref( warehouse.settlement )
		self.widgets.append(entry)

		settlement_name_label = entry.findChild(name="warehouse_name")
		settlement_name_label.text = warehouse.settlement.get_component(NamedComponent).name
		player_name_label = entry.findChild(name="player_name")
		player_name_label.text = warehouse.owner.name

		self.add_trade_slots(entry, self.slots_per_entry)

		index = 1
		resource_list = resource_list or {}
		for res_id in resource_list:
			if index > self.slots_per_entry:
				break
			self.add_resource(slot=self.slots[entry][index - 1],
			                  res_id=res_id,
			                  entry=entry,
			                  has_value=True,
			                  value=resource_list[res_id])
			index += 1

		entry.mapEvents({
		  'delete_warehouse/mouseClicked' : Callback(self.remove_entry, entry),
		  'move_up/mouseClicked' : Callback(self.move_entry, entry, 'up'),
		  'move_down/mouseClicked' : Callback(self.move_entry, entry, 'down')
		  })
		vbox.addChild(entry)

	def append_warehouse(self, warehouse):
		"""Add a warehouse to the list on the left side.
		@param warehouse: Set to add a specific one, else the selected one gets added.
		"""
		if not self.session.world.diplomacy.can_trade(self.session.world.player, warehouse.owner):
			self.session.ingame_gui.message_widget.add_custom(point=None, messagetext=_("You are not allowed to trade with this player"))
			return

		if len(self.widgets) >= self.MAX_ENTRIES:
			# reached max entries the gui can hold
			AmbientSoundComponent.play_special('error')
			return

		self._route_cmd("append", warehouse.worldid)
		self.add_gui_entry(warehouse)
		if self.resource_menu_shown:
			self.hide_resource_menu()

		self._check_no_entries_label()

		self._gui.adaptLayout()

	def _init_gui(self):
		"""
		Initial init of gui.
		widgets : list of route entry widgets
		slots : dict with slots for each entry
		"""
		self._gui = load_uh_widget("configure_route.xml")

		self.widgets = []
		self.slots = {}
		self.slots_per_entry = 3

		icon = self._gui.findChild(name="minimap")
		def on_click(event, drag):
			if drag:
				return
			if event.getButton() == fife.MouseEvent.LEFT:
				map_coord = event.map_coord
				tile = self.session.world.get_tile(Point(*map_coord))
				if tile is not None and tile.settlement is not None:
					self.append_warehouse( tile.settlement.warehouse )

		self.minimap = Minimap(icon, session=self.session,
		                       world=self.session.world,
		                       view=self.session.view,
		                       targetrenderer=horizons.globals.fife.targetrenderer,
		                       imagemanager=horizons.globals.fife.imagemanager,
		                       cam_border=False,
		                       use_rotation=False,
		                       on_click=on_click)

		resources = self.session.db.get_res_id_and_icon(only_tradeable=True)
		# map an icon for a resource
		# map a resource for an icon
		self.resource_for_icon = {}
		self.icon_for_resource = {}
		for res_id, icon in list(resources) + [(0, self.dummy_icon_path)]:
			self.resource_for_icon[icon] = res_id
			self.icon_for_resource[res_id] = icon

		# don't do any actions if the resource menu is shown
		self.resource_menu_shown = False
		for entry in self.instance.route.waypoints:
			self.add_gui_entry(entry['warehouse'], entry['resource_list'])

		self._check_no_entries_label()

		wait_at_unload_box = self._gui.findChild(name="wait_at_unload")
		wait_at_unload_box.marked = self.instance.route.wait_at_unload
		def toggle_wait_at_unload():
			self._route_cmd("set_wait_at_unload", not self.instance.route.wait_at_unload)
		wait_at_unload_box.capture(toggle_wait_at_unload)

		wait_at_load_box = self._gui.findChild(name="wait_at_load")
		wait_at_load_box.marked = self.instance.route.wait_at_load
		def toggle_wait_at_load():
			self._route_cmd("set_wait_at_load", not self.instance.route.wait_at_load)
		wait_at_load_box.capture(toggle_wait_at_load)

		self._gui.mapEvents({
		  OkButton.DEFAULT_NAME : self.hide,
		  'start_route/mouseClicked' : self.toggle_route
		  })
		self._gui.position_technique = "automatic" # "center:center"

		"""
		import cProfile as profile
		import tempfile
		outfilename = tempfile.mkstemp(text=True)[1]
		print 'profile to ', outfilename
		profile.runctx( "self.minimap.draw()", globals(), locals(), outfilename)
		"""


	def _route_cmd(self, method, *args, **kwargs):
		"""Convenience method for calling a method on instance.route via command (mp-safe)"""
		RouteConfigCommand(self.instance, method, *args, **kwargs).execute(self.session)

