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
from horizons.util import WorldObject
from horizons.util.lastactiveplayersettlementmanager import LastActivePlayerSettlementManager
from horizons.constants import LAYERS

from fife.extensions.pychan import widgets

class NavigationTool(CursorTool):
	"""Navigation Class to process mouse actions ingame"""

	last_event_pos = None # last received mouse event position, fife.ScreenPoint

	def __init__(self, session):
		super(NavigationTool, self).__init__(session)
		self._last_mmb_scroll_point = [0, 0]
		self.lastmoved = fife.ExactModelCoordinate()
		self.middle_scroll_active = False

		class CmdListener(fife.ICommandListener): pass
		self.cmdlist = CmdListener()
		horizons.main.fife.eventmanager.addCommandListener(self.cmdlist)
		self.cmdlist.onCommand = self.onCommand

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

				# can't import Icon directly since it won't have tooltips
				# TODO: find a way to make this obvious
				self.icon = widgets.WIDGETS['Icon']()

			def toggle(self):
				self.enabled = not self.enabled
				if not self.enabled and self.icon.tooltip_shown:
					self.icon.hide_tooltip()

			def show_evt(self, evt):
				if self.enabled:
					x, y = self.cursor_tool.get_world_location_from_event(evt).to_tuple()
					self.icon.helptext = str(x) + ', ' + str(y) + " "+_("Press H to remove this hint")
					self.icon.position_tooltip(evt)
					self.icon.show_tooltip()

		self.tooltip = CoordsTooltip.get_instance(self)

	def remove(self):
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
		current = self.get_exact_world_location_from_event(evt)
		if abs((current.x-self.lastmoved.x)**2+(current.y-self.lastmoved.y)**2) >= 4**2: # move was far enough, 4 px
			self.lastmoved = current
			# update res bar with settlement-related info
			LastActivePlayerSettlementManager().update(current)

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
		self.session.view.zoom_in(True)
		evt.consume()

	# move down mouse wheel = zoom out
	def mouseWheelMovedDown(self, evt):
		self.session.view.zoom_out(True)
		evt.consume()

	def onCommand(self, command):
		if command.getCommandType() == fife.CMD_APP_ICONIFIED or command.getCommandType() == fife.CMD_INPUT_FOCUS_LOST:
			self.session.view.autoscroll(0, 0) #stop autoscroll

	def get_hover_instances(self, evt, layers=None):
		"""
		Utility method, returns the instances under the cursor
		@param layers: list of layer ids to search for. Default to OBJECTS
		"""
		if layers is None:
			layers = [LAYERS.OBJECTS]


		all_instances = []
		for layer in layers:
			instances = self.session.view.cam.getMatchingInstances(\
		    fife.ScreenPoint(evt.getX(), evt.getY()), self.session.view.layers[layer], False) # False for accurate
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
		self.helptext = None
