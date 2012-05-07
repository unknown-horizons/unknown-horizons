# -*- coding: utf-8 -*-
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
import horizons.main

from horizons.gui.mousetools.cursortool import CursorTool
from horizons.util import WorldObject, WeakList
from horizons.util.lastactiveplayersettlementmanager import LastActivePlayerSettlementManager
from horizons.constants import LAYERS
from horizons.messaging import HoverInstancesChanged
from horizons.messaging import MessageBus
from horizons.extscheduler import ExtScheduler

from fife.extensions.pychan.widgets import Icon

class NavigationTool(CursorTool):
	"""Navigation Class to process mouse actions ingame"""

	last_event_pos = fife.ScreenPoint(0, 0) # last received mouse event position, fife.ScreenPoint

	send_hover_instances_update = True
	HOVER_INSTANCES_UPDATE_DELAY = 1 # sec
	last_hover_instances = WeakList()

	def __init__(self, session):
		super(NavigationTool, self).__init__(session)
		self._last_mmb_scroll_point = [0, 0]
		# coordinates of last mouse positions
		self.last_exact_world_location = fife.ExactModelCoordinate()
		self._hover_instances_update_scheduled = False
		self.middle_scroll_active = False

		class CmdListener(fife.ICommandListener): pass
		self.cmdlist = CmdListener()
		horizons.main.fife.eventmanager.addCommandListener(self.cmdlist)
		self.cmdlist.onCommand = self.onCommand

		if not self.__class__.send_hover_instances_update:
			# clear
			HoverInstancesChanged.broadcast(self, set())
			self.__class__.last_hover_instances = WeakList()
		else:
			# need updates about scrolling here
			self.session.view.add_change_listener(self._schedule_hover_instance_update)
			self._schedule_hover_instance_update()

		class CoordsTooltip(object):
			@classmethod
			def get_instance(cls, cursor_tool):
				if cursor_tool.session.coordinates_tooltip is not None:
					inst = cursor_tool.session.coordinates_tooltip
					inst.cursor_tool = cursor_tool
					return inst
				else:
					return CoordsTooltip(cursor_tool)

			def __init__(self, cursor_tool, **kwargs):
				super(CoordsTooltip, self).__init__(**kwargs)
				cursor_tool.session.coordinates_tooltip = self
				self.cursor_tool = cursor_tool
				self.enabled = False

				self.icon = Icon(position=(1,1)) # 0, 0 is currently not supported by tooltips


			def toggle(self):
				self.enabled = not self.enabled
				if not self.enabled and self.icon.tooltip_shown:
					self.icon.hide_tooltip()

			def show_evt(self, evt):
				if self.enabled:
					x, y = self.cursor_tool.get_world_location(evt).to_tuple()
					self.icon.helptext = u'%f, %f ' % (x, y) + _("Press H to remove this hint")
					self.icon.position_tooltip(evt)
					self.icon.show_tooltip()

		self.tooltip = CoordsTooltip.get_instance(self)

	def remove(self):
		if self.__class__.send_hover_instances_update:
			self.session.view.remove_change_listener(self._schedule_hover_instance_update)
		horizons.main.fife.eventmanager.removeCommandListener(self.cmdlist)
		super(NavigationTool, self).remove()

	def mousePressed(self, evt):
		if (evt.getButton() == fife.MouseEvent.MIDDLE):
			self._last_mmb_scroll_point = (evt.getX(), evt.getY())
			self.middle_scroll_active = True

	def mouseReleased(self, evt):
		if (evt.getButton() == fife.MouseEvent.MIDDLE):
			self.middle_scroll_active = False

	def mouseDragged(self, evt):
		if (evt.getButton() == fife.MouseEvent.MIDDLE):
			if self.middle_scroll_active:
				scroll_by = ( self._last_mmb_scroll_point[0] - evt.getX(),
				              self._last_mmb_scroll_point[1] - evt.getY() )
				self.session.view.scroll( *scroll_by )
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

		self.tooltip.show_evt(evt)
		mousepoint = fife.ScreenPoint(evt.getX(), evt.getY())
		self.__class__.last_event_pos = mousepoint

		# Status menu update
		current = self.get_exact_world_location(evt)

		distance_ge = lambda a, b, epsilon : abs((a.x-b.x)**2 + (a.y-b.y)**2) >= epsilon**2

		if distance_ge(current, self.last_exact_world_location, 4): # update every 4 tiles for settlement info
			self.last_exact_world_location = current
			# update res bar with settlement-related info
			LastActivePlayerSettlementManager().update(current)

		# check if instance update is scheduled
		if self.__class__.send_hover_instances_update:
			self._schedule_hover_instance_update()

		# Mouse scrolling
		x, y = 0, 0
		if mousepoint.x < 5:
			x -= 5 - mousepoint.x
		elif mousepoint.x >= (self.session.view.cam.getViewPort().right()-5):
			x += 6 + mousepoint.x - self.session.view.cam.getViewPort().right()
		if mousepoint.y < 5:
			y -= 5 - mousepoint.y
		elif mousepoint.y >= (self.session.view.cam.getViewPort().bottom()-5):
			y += 6 + mousepoint.y - self.session.view.cam.getViewPort().bottom()
		x *= 10
		y *= 10
		self.session.view.autoscroll(x, y)

	# move up mouse wheel = zoom in
	def mouseWheelMovedUp(self, evt):
		if horizons.main.fife.get_uh_setting("CursorCenteredZoom"):
			self.session.view.zoom_in(True)
		else:
			self.session.view.zoom_in(False)
		evt.consume()

	# move down mouse wheel = zoom out
	def mouseWheelMovedDown(self, evt):
		if horizons.main.fife.get_uh_setting("CursorCenteredZoom"):
			self.session.view.zoom_out(True)
		else:
			self.session.view.zoom_out(False)
		evt.consume()

	def onCommand(self, command):
		"""Called when some kind of command-event happens.
		For "documentation", see:
		engine/core/eventchannel/command/ec_commandids.h
		engine/core/eventchannel/eventmanager.cpp
		in fife.
		It's usually about mouse/keyboard focus or window being iconified/restored.
		"""
		STOP_SCROLLING_ON = (fife.CMD_APP_ICONIFIED,
		                     fife.CMD_MOUSE_FOCUS_LOST,
		                     fife.CMD_INPUT_FOCUS_LOST)
		if command.getCommandType() in STOP_SCROLLING_ON:
			# a random, unreproducible crash has session set to None. Check because it doesn't hurt.
			if self.session is not None:
				self.session.view.autoscroll(0, 0) # stop autoscroll

	def get_hover_instances(self, where, layers=None):
		"""
		Utility method, returns the instances under the cursor
		@param where: anything supporting getX/getY
		@param layers: list of layer ids to search for. Default to OBJECTS
		"""
		if layers is None:
			layers = [LAYERS.OBJECTS]

		all_instances = []
		for layer in layers:
			instances = self.session.view.cam.getMatchingInstances(\
		    fife.ScreenPoint(where.getX(), where.getY()), self.session.view.layers[layer], False) # False for accurate
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
		super(NavigationTool, self).end()
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
		where = fife.Point(self.last_event_pos.x, self.last_event_pos.y)
		instances = set(self.get_hover_instances(where))
		# only send when there were actual changes
		if instances != set(self.__class__.last_hover_instances):
			self.__class__.last_hover_instances = WeakList(instances)
			HoverInstancesChanged.broadcast(self, instances)
