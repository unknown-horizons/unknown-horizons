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

from fife import fife
from fife.extensions.pychan.widgets import Icon

import horizons.globals
from horizons.constants import LAYERS, VIEW
from horizons.extscheduler import ExtScheduler
from horizons.gui.mousetools.cursortool import CursorTool
from horizons.i18n import gettext as T
from horizons.messaging import HoverInstancesChanged
from horizons.util.lastactiveplayersettlementmanager import LastActivePlayerSettlementManager
from horizons.util.python.weaklist import WeakList
from horizons.util.worldobject import WorldObject


class NavigationTool(CursorTool):
	"""Navigation Class to process mouse actions ingame"""

	last_event_pos = fife.ScreenPoint(0, 0) # last received mouse event position, fife.ScreenPoint

	send_hover_instances_update = True
	HOVER_INSTANCES_UPDATE_DELAY = 1 # sec
	last_hover_instances = WeakList()

	consumed_by_widgets = False

	def __init__(self, session):
		super().__init__(session)
		self.setGlobalListener(True)
		self._last_mmb_scroll_point = [0, 0]
		# coordinates of last mouse positions
		self.last_exact_world_location = fife.ExactModelCoordinate()
		self._hover_instances_update_scheduled = False
		self.middle_scroll_active = False

		class CmdListener(fife.ICommandListener):
			pass
		self.cmdlist = CmdListener()
		horizons.globals.fife.eventmanager.addCommandListener(self.cmdlist)
		self.cmdlist.onCommand = self.onCommand

		if not self.__class__.send_hover_instances_update:
			# clear
			HoverInstancesChanged.broadcast(self, set())
			self.__class__.last_hover_instances = WeakList()
		else:
			# need updates about scrolling here
			self.session.view.add_change_listener(self._schedule_hover_instance_update)
			self._schedule_hover_instance_update()

		class CoordsTooltip:
			@classmethod
			def get_instance(cls, cursor_tool):
				if cursor_tool.session.ingame_gui.coordinates_tooltip is not None:
					inst = cursor_tool.session.ingame_gui.coordinates_tooltip
					inst.cursor_tool = cursor_tool
					return inst
				else:
					return CoordsTooltip(cursor_tool)

			def __init__(self, cursor_tool, **kwargs):
				super().__init__(**kwargs)
				cursor_tool.session.ingame_gui.coordinates_tooltip = self
				self.cursor_tool = cursor_tool
				self.enabled = False

				self.icon = Icon(position=(1, 1)) # 0, 0 is currently not supported by tooltips

			def toggle(self):
				self.enabled = not self.enabled
				if not self.enabled and self.icon.tooltip_shown:
					self.icon.hide_tooltip()

			def show_evt(self, evt):
				if self.enabled:
					if evt.isConsumedByWidgets():
						if self.icon.tooltip_shown:
							self.icon.hide_tooltip()
						return
					x, y = self.cursor_tool.get_world_location(evt).to_tuple()
					self.icon.helptext = '{:d}, {:d} '.format(x, y) + T("Press H to remove this hint")
					self.icon.position_tooltip(evt)
					self.icon.show_tooltip()

		self.tooltip = CoordsTooltip.get_instance(self)

	def remove(self):
		if self.__class__.send_hover_instances_update:
			self.session.view.remove_change_listener(self._schedule_hover_instance_update)
		if self._hover_instances_update_scheduled:
			ExtScheduler().rem_call(self, self._send_hover_instance_upate)

		horizons.globals.fife.eventmanager.removeCommandListener(self.cmdlist)
		super().remove()

	def mousePressed(self, evt):
		if evt.getButton() == fife.MouseEvent.MIDDLE:
			if horizons.globals.fife.get_uh_setting("MiddleMousePan"):
				self._last_mmb_scroll_point = (evt.getX(), evt.getY())
				self.middle_scroll_active = True

	def mouseReleased(self, evt):
		if evt.getButton() == fife.MouseEvent.MIDDLE:
			if horizons.globals.fife.get_uh_setting("MiddleMousePan"):
				self.middle_scroll_active = False

	def mouseDragged(self, evt):
		self.consumed_by_widgets = evt.isConsumedByWidgets()
		if evt.getButton() == fife.MouseEvent.MIDDLE:
			if horizons.globals.fife.get_uh_setting("MiddleMousePan"):
				if self.middle_scroll_active:
					scroll_by = (self._last_mmb_scroll_point[0] - evt.getX(),
					             self._last_mmb_scroll_point[1] - evt.getY())
					self.session.view.scroll(*scroll_by)
					self._last_mmb_scroll_point = (evt.getX(), evt.getY())
		else:
			# Else the event will mistakenly be delegated if the left mouse button is hit while
			# scrolling using the middle mouse button
			if not self.middle_scroll_active:
				NavigationTool.mouseMoved(self, evt)

	# return new mouse position after moving
	def mouseMoved(self, evt):
		if not self.session.world.inited:
			return

		self.consumed_by_widgets = evt.isConsumedByWidgets()

		self.tooltip.show_evt(evt)
		# don't overwrite this last_event_pos instance. Due to class
		# hierarchy, it would write to the lowest class (e.g. SelectionTool)
		# and the attribute in NavigationTool would be left unchanged.
		self.__class__.last_event_pos.set(evt.getX(), evt.getY(), 0)
		mousepoint = self.__class__.last_event_pos

		# Status menu update
		current = self.get_exact_world_location(evt)

		distance_ge = lambda a, b, epsilon: abs((a.x - b.x) ** 2 + (a.y - b.y) ** 2) >= epsilon ** 2

		if distance_ge(current, self.last_exact_world_location, 4): # update every 4 tiles for settlement info
			self.last_exact_world_location = current
			# update res bar with settlement-related info
			LastActivePlayerSettlementManager().update(current)

		# check if instance update is scheduled
		if self.__class__.send_hover_instances_update:
			self._schedule_hover_instance_update()

		# Mouse scrolling
		x, y = 0, 0
		if mousepoint.x < VIEW.AUTOSCROLL_WIDTH:
			x -= VIEW.AUTOSCROLL_WIDTH - mousepoint.x
		elif mousepoint.x > (self.session.view.cam.getViewPort().right() - VIEW.AUTOSCROLL_WIDTH):
			x += VIEW.AUTOSCROLL_WIDTH + mousepoint.x - self.session.view.cam.getViewPort().right()
		if mousepoint.y < VIEW.AUTOSCROLL_WIDTH:
			y -= VIEW.AUTOSCROLL_WIDTH - mousepoint.y
		elif mousepoint.y > (self.session.view.cam.getViewPort().bottom() - VIEW.AUTOSCROLL_WIDTH):
			y += VIEW.AUTOSCROLL_WIDTH + mousepoint.y - self.session.view.cam.getViewPort().bottom()
		x *= 10
		y *= 10
		self.session.view.autoscroll(x, y)

	# move up mouse wheel = zoom in
	def mouseWheelMovedUp(self, evt):
		track_cursor = horizons.globals.fife.get_uh_setting("CursorCenteredZoom")
		self.session.view.zoom_in(track_cursor)
		evt.consume()

	# move down mouse wheel = zoom out
	def mouseWheelMovedDown(self, evt):
		track_cursor = horizons.globals.fife.get_uh_setting("CursorCenteredZoom")
		self.session.view.zoom_out(track_cursor)
		evt.consume()

	def onCommand(self, command):
		"""Called when some kind of command-event happens.
		For "documentation", see:
		engine/core/eventchannel/command/ec_commandids.h
		engine/core/eventchannel/eventmanager.cpp
		in fife.
		It's usually about mouse/keyboard focus or window being iconified/restored.
		"""
		stop_scrolling_on = (fife.CMD_APP_ICONIFIED,
		                     fife.CMD_MOUSE_FOCUS_LOST,
		                     fife.CMD_INPUT_FOCUS_LOST)
		if command.getCommandType() in stop_scrolling_on:
			# it has been randomly observed twice that this code is reached with session being None or
			# partly deinitialized. Since it is unknown how fife handles this and why
			# removeCommandListener in remove() doesn't prevent further calls, we have to catch and ignore the error
			try:
				self.session.view.autoscroll(0, 0) # stop autoscroll
			except AttributeError:
				pass

	def get_hover_instances(self, where, layers=None):
		"""
		Utility method, returns the instances under the cursor
		@param where: anything supporting getX/getY
		@param layers: list of layer ids to search for. Default to OBJECTS
		"""

		if self.consumed_by_widgets:
			return []

		if layers is None:
			layers = [LAYERS.OBJECTS]

		all_instances = []
		for layer in layers:
			x = where.getX()
			y = where.getY()
			instances = self.session.view.cam.getMatchingInstances(
				fife.ScreenPoint(x, y),
				self.session.view.layers[layer], False) # False for accurate

			# if no instances found, try again and search within a 8px radius
			if not instances:
				selection_radius = 8
				radius = fife.Rect(x - selection_radius, y - selection_radius,
				                   selection_radius * 2, selection_radius * 2)

				instances = self.session.view.cam.getMatchingInstances(radius,
									self.session.view.layers[layer])

			all_instances.extend(instances)

		hover_instances = []
		for i in all_instances:
			id = i.getId()
			# Check id, can be '' if instance is created and clicked on before
			# actual game representation class is created (network play)
			if id == '':
				continue
			instance = WorldObject.get_object_by_id(int(id))
			hover_instances.append(instance)
		return hover_instances

	def end(self):
		super().end()
		if self._hover_instances_update_scheduled:
			ExtScheduler().rem_all_classinst_calls(self)
		self.helptext = None

	def _schedule_hover_instance_update(self):
		"""Hover instances have potentially changed, do an update in a timely fashion (but not right away)"""
		if not self._hover_instances_update_scheduled:
			self._hover_instances_update_scheduled = True
			ExtScheduler().add_new_object(self._send_hover_instance_upate, self,
			                              run_in=self.__class__.HOVER_INSTANCES_UPDATE_DELAY)

	def _send_hover_instance_upate(self):
		"""Broadcast update with new instances below mouse (hovered).
		At most called in a certain interval, not after every mouse move in
		order to prevent delays."""
		self._hover_instances_update_scheduled = False
		where = fife.Point(self.__class__.last_event_pos.x, self.__class__.last_event_pos.y)

		instances = set(self.get_hover_instances(where))
		# only send when there were actual changes
		if instances != set(self.__class__.last_hover_instances):
			self.__class__.last_hover_instances = WeakList(instances)
			HoverInstancesChanged.broadcast(self, instances)
