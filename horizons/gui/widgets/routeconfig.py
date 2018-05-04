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
import weakref

from fife import fife
from fife.extensions.pychan import widgets

import horizons.globals
from horizons.command.uioptions import RouteConfigCommand
from horizons.command.unit import CreateRoute
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.component.namedcomponent import NamedComponent
from horizons.component.storagecomponent import StorageComponent
from horizons.constants import STORAGE
from horizons.gui.util import create_resource_selection_dialog, get_res_icon_path, load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton
from horizons.gui.widgets.minimap import Minimap
from horizons.gui.windows import Window
from horizons.i18n import gettext as T
from horizons.manager import MPManager
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback
from horizons.util.shapes import Point


class RouteConfig(Window):
	"""
	Widget that allows configurating a ship's trading route
	"""
	dummy_icon_path = "content/gui/icons/resources/none_gray.png"
	buy_button_path = "content/gui/images/tabwidget/warehouse_to_ship.png"
	sell_button_path = "content/gui/images/tabwidget/ship_to_warehouse.png"
	MAX_ENTRIES = 5
	MIN_ENTRIES = 2
	SLOTS_PER_ENTRY = 4

	def __init__(self, windows, instance):
		super().__init__(windows)

		self.instance = instance

		if not hasattr(instance, 'route'):
			CreateRoute(instance).execute(self.session)

			# We must make sure that the createRoute command has successfully finished, even in network games.
			Scheduler().add_new_object(self._init_gui, self, run_in=MPManager.EXECUTIONDELAY + 2)
		else:
			self._init_gui()

	@property
	def session(self):
		"""
		@rtype session: horizons.session.Session
		@return: session
		"""
		session = self.instance.session
		assert isinstance(session, horizons.session.Session)
		return session

	def show(self):
		self.minimap.draw()
		self._gui.show()

		self.instance.add_remove_listener(self.on_instance_removed, no_duplicates=True)
		self.instance.route.add_change_listener(self.on_route_change, no_duplicates=True, call_listener_now=True)

	def hide(self):
		# Check if the deferred init_gui call in __init__ ran already, otherwise cancel it
		if not hasattr(self, '_gui'):
			Scheduler().rem_call(self, self._init_gui)
			return

		self.minimap.disable()
		self._gui.hide()

		self.instance.discard_remove_listener(self.on_instance_removed)
		self.instance.route.discard_remove_listener(self.on_route_change)

		# make sure user knows that it's not enabled (if it appears to be complete)
		if not self.instance.route.enabled and self.instance.route.can_enable():
			# If message_widget is not defined anymore, we're closing the game right
			# now
			if self.session.ingame_gui.message_widget:
				self.session.ingame_gui.message_widget.add('ROUTE_DISABLED')

	def on_instance_removed(self):
		self._windows.close()
		self.instance = None

	def on_route_change(self):
		"""Called on changelistener notifications from the route"""
		if self.instance.route.enabled:
			self.start_button_set_inactive()
		else:
			self.start_button_set_active()

	def start_button_set_active(self):
		self._gui.findChild(name='start_route').set_active()
		self._gui.findChild(name='start_route').helptext = T('Start route')

	def start_button_set_inactive(self):
		self._gui.findChild(name='start_route').set_inactive()
		self._gui.findChild(name='start_route').helptext = T('Stop route')

	def start_route(self):
		if self.instance.route.can_enable():
			self._route_cmd("enable")
		else:
			self.instance.session.ingame_gui.open_popup(
				T("Need at least two settlements"),
				T("You need at least two different settlements in your route."))

	def stop_route(self):
		self._route_cmd("disable")

	def toggle_route(self):
		if not self.instance.route.enabled:
			self.start_route()
		else:
			self.stop_route()

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
			lbl = widgets.Label(name=name, text=T("Click on a settlement to add a waypoint!"))
			self._gui.findChild(name="left_vbox").addChild(lbl)
		else:
			lbl = self._gui.findChild(name=name)
			if lbl:
				self._gui.findChild(name="left_vbox").removeChild(lbl)

	def move_entry(self, entry, direction):
		"""
		moves an entry up or down
		"""
		# Abort (with error sound) if moving this entry is not possible.
		position = self.widgets.index(entry)
		if position == len(self.widgets) and direction == 'down' or \
		   position == 0 and direction == 'up':
			AmbientSoundComponent.play_special('error')
			return

		if direction == 'up':
			new_pos = position - 1
		elif direction == 'down':
			new_pos = position + 1
		else:
			assert False, 'Direction for `move_entry` is neither "up" nor "down".'

		vbox = self._gui.findChild(name="left_vbox")

		vbox.removeChildren(self.widgets)
		self.widgets.insert(new_pos, self.widgets.pop(position))
		self._route_cmd("move_waypoint", position, direction)
		vbox.addChildren(self.widgets)

		self._gui.adaptLayout()

	def show_load_icon(self, slot):
		button = slot.findChild(name="buysell")
		button.up_image = self.buy_button_path
		button.helptext = T("Loading into ship")
		slot.action = "load"

	def show_unload_icon(self, slot):
		button = slot.findChild(name="buysell")
		button.up_image = self.sell_button_path
		button.helptext = T("Unloading from ship")
		slot.action = "unload"

	def toggle_load_unload(self, slot, entry):
		position = self.widgets.index(entry)
		res_button = slot.findChild(name="button")
		res = self.resource_for_icon[res_button.up_image.source]

		if res != 0:
			self._route_cmd("toggle_load_unload", position, res)

		if slot.action == "unload":
			self.show_load_icon(slot)
		else:
			self.show_unload_icon(slot)

	def slider_adjust(self, slot, res_id, entry):
		position = self.widgets.index(entry)
		slider = slot.findChild(name="slider")
		amount_lbl = slot.findChild(name="amount")
		amount = int(slider.value)
		amount_lbl.text = '{amount}t'.format(amount=amount)
		if slot.action == "unload":
			amount = -amount
		self._route_cmd("add_to_resource_list", position, res_id, amount)
		slot.adaptLayout()

	def add_resource(self, res_id, slot=None, entry=None, has_value=False, value=0):
		button = slot.findChild(name="button")
		position = self.widgets.index(entry)
		# Remove old resource from waypoints.
		res = self.resource_for_icon[button.up_image.source]
		if res != 0:
			self._route_cmd("remove_from_resource_list", position, res)

		icon = self.icon_for_resource[res_id]
		button.up_image, button.down_image, button.hover_image = icon, icon, icon
		button.fixed_size = (32, 32)

		# Hide the resource menu.
		self.hide_resource_menu()

		# Show widget elements for new resource.
		slider = slot.findChild(name="slider")

		if not has_value:
			value = int(slider.value)
			if slot.action == "unload":
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
			# Keep the load/unload persistent if the slider value is 0.
			slider.value = 0.
			amount = value

		if res_id != 0:
			slot.findChild(name="amount").text = str(amount) + "t"
			slot.adaptLayout()
			self._route_cmd("add_to_resource_list", position, res_id, value)
			slider.capture(Callback(self.slider_adjust, slot, res_id, entry))
		else:
			slot.findChild(name="amount").text = ""

	def handle_resource_click(self, widget, event):
		if event.getButton() == fife.MouseEvent.LEFT:
			self.show_resource_menu(widget.parent, widget.parent.parent)
		elif event.getButton() == fife.MouseEvent.RIGHT:
			if self.resource_menu_shown:
				# abort resource selection (#1310)
				self.hide_resource_menu()
			else:
				# remove the load/unload order
				self.add_resource(slot=widget.parent, res_id=0, entry=widget.parent.parent)

	def show_resource_menu(self, slot, entry):
		"""
		Displays a menu where players can choose which resource to add in the
		selected slot. Available resources are all possible resources and a
		'None' resource which allows to delete slot actions.
		The resources are ordered by their res_id.
		"""

		position = self.widgets.index(entry)
		if self.resource_menu_shown:
			self.hide_resource_menu()
		self.resource_menu_shown = True

		on_click = functools.partial(self.add_resource, slot=slot, entry=entry)
		settlement = entry.settlement()
		inventory = settlement.get_component(StorageComponent).inventory if settlement else None
		widget = "scrollbar_resource_selection.xml"

		def res_filter(res_id):
			same_icon = slot.findChild(name='button').up_image.source == self.icon_for_resource[res_id]
			already_listed = res_id in self.instance.route.waypoints[position]['resource_list']
			return not (same_icon or already_listed)

		dlg = create_resource_selection_dialog(on_click=on_click, inventory=inventory,
			db=self.session.db, widget=widget, amount_per_line=5, res_filter=res_filter)

		self._gui.findChild(name="resources_scrollarea").addChild(dlg)
		self._gui.adaptLayout()

	def hide_resource_menu(self):
		self.resource_menu_shown = False
		self._gui.findChild(name="resources_scrollarea").removeAllChildren()

	def add_trade_slots(self, entry, slot_amount=SLOTS_PER_ENTRY):
		x_position = 0
		y_position = 23
		# Initialize slots with empty dict.
		self.slots[entry] = {}
		for num in range(slot_amount):
			slot = load_uh_widget('trade_single_slot.xml')
			slot.name = 'slot_{:d}'.format(num)
			slot.position = (x_position, y_position)

			slot.action = "load"

			slider = slot.findChild(name="slider")
			slider.scale_start = 0.0
			slider.scale_end = float(
				min(self.instance.get_component(StorageComponent).inventory.limit,
					STORAGE.ITEMS_PER_TRADE_SLOT))

			slot.findChild(name="buysell").capture(Callback(self.toggle_load_unload, slot, entry))

			button = slot.findChild(name="button")
			button.capture(self.handle_resource_click, event_name='mouseClicked')
			button.up_image = self.dummy_icon_path
			button.down_image = self.dummy_icon_path
			button.hover_image = self.dummy_icon_path

			icon = slot.findChild(name="icon")
			fillbar = slot.findChild(name="fillbar")
			fillbar.position = (icon.width - fillbar.width - 1, icon.height)
			x_position += 60

			entry.addChild(slot)
			self.slots[entry][num] = slot
			self.show_load_icon(slot)

	def add_gui_entry(self, warehouse, resource_list=None):
		vbox = self._gui.findChild(name="left_vbox")
		entry = load_uh_widget("route_entry.xml")
		entry.name = 'container_{:d}'.format(len(self.widgets))
		entry.settlement = weakref.ref(warehouse.settlement)
		self.widgets.append(entry)

		settlement_name_label = entry.findChild(name="warehouse_name")
		warehouse_name = warehouse.settlement.get_component(NamedComponent).name

		# Limit displayed settlement name length to avoid collision with trade slots
		if len(warehouse_name) > 14:
			warehouse_name = warehouse_name[:14] + "..."
		settlement_name_label.text = warehouse_name

		player_name_label = entry.findChild(name="player_name")
		player_name = warehouse.owner.name

		# Limit displayed player name length to avoid collision with trade slots
		if len(player_name) > 18:
			player_name = player_name[:18] + "..."
		player_name_label.text = player_name

		self.add_trade_slots(entry)

		index = 1
		resource_list = resource_list or {}
		for res_id in resource_list:
			if index > self.SLOTS_PER_ENTRY:
				break
			self.add_resource(slot=self.slots[entry][index - 1],
			                  res_id=res_id,
			                  entry=entry,
			                  has_value=True,
			                  value=resource_list[res_id])
			index += 1

		entry.mapEvents({
		  'delete_warehouse/mouseClicked': Callback(self.remove_entry, entry),
		  'move_up/mouseClicked': Callback(self.move_entry, entry, 'up'),
		  'move_down/mouseClicked': Callback(self.move_entry, entry, 'down')
		  })
		vbox.addChild(entry)

	def append_warehouse(self, warehouse):
		"""Add a warehouse to the list on the left side.
		@param warehouse: Set to add a specific one, else the selected one gets added.
		"""
		if not self.session.world.diplomacy.can_trade(self.session.world.player, warehouse.owner):
			self.session.ingame_gui.message_widget.add_custom(T("You are not allowed to trade with this player"))
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

	def on_map_click(self, event, drag):
		if drag:
			return
		if event.getButton() == fife.MouseEvent.LEFT:
			map_coords = event.map_coords
			tile = self.session.world.get_tile(Point(*map_coords))
			if tile is not None and tile.settlement is not None:
				self.append_warehouse(tile.settlement.warehouse)

	def _init_gui(self):
		"""
		Initial init of gui.
		widgets : list of route entry widgets
		slots : dict with slots for each entry
		"""
		self._gui = load_uh_widget("configure_route.xml", center_widget=True)

		self.widgets = []
		self.slots = {}

		icon = self._gui.findChild(name="minimap")

		self.minimap = Minimap(icon, session=self.session,
		                       world=self.session.world,
		                       view=self.session.view,
		                       targetrenderer=horizons.globals.fife.targetrenderer,
		                       imagemanager=horizons.globals.fife.imagemanager,
		                       cam_border=False,
		                       use_rotation=False,
		                       on_click=self.on_map_click)

		resources = self.session.db.get_res(only_tradeable=True)
		# map an icon for a resource
		# map a resource for an icon
		self.resource_for_icon = {self.dummy_icon_path: 0}
		self.icon_for_resource = {0: self.dummy_icon_path}
		for res_id in resources:
			icon = get_res_icon_path(res_id)
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
			OkButton.DEFAULT_NAME: self._windows.close,
			'start_route/mouseClicked': self.toggle_route,
		})

	def _route_cmd(self, method, *args, **kwargs):
		"""Convenience method for calling a method on instance.route via command (mp-safe)"""
		RouteConfigCommand(self.instance, method, *args, **kwargs).execute(self.session)
