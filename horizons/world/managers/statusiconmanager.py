# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.

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

import horizons.globals

from fife import fife
from fife.extensions.pychan.widgets import Icon

from horizons.world.managers.abstracticonmanager import AbstractIconManager
from horizons.world.status import StatusIcon
from horizons.messaging import AddStatusIcon, RemoveStatusIcon, WorldObjectDeleted, HoverInstancesChanged
from horizons.gui.mousetools import NavigationTool

class StatusIconManager(AbstractIconManager):
	"""Manager class that manages all status icons. It listenes to AddStatusIcon
	and RemoveStatusIcon messages on the main message bus"""

	def __init__(self, renderer, layer):
		"""
		@param renderer: Renderer used to render the icons
		@param layer: map layer, needed to place icon
		"""
		super(StatusIconManager, self).__init__(renderer, layer)

		# {instance: [list of icons]}
		self.icons = {}

		self.tooltip_instance = None # no weakref:
		# we need to remove the tooltip always anyway, and along with it the entry here
		self.tooltip_icon = Icon(position=(1, 1)) # 0, 0 is currently not supported by tooltips

		AddStatusIcon.subscribe(self.on_add_icon_message)
		HoverInstancesChanged.subscribe(self.on_hover_instances_changed)
		RemoveStatusIcon.subscribe(self.on_remove_icon_message)
		WorldObjectDeleted.subscribe(self.on_worldobject_deleted_message)

	def end(self):
		self.tooltip_instance = None
		self.tooltip_icon.hide_tooltip()
		self.tooltip_icon = None

		super(StatusIconManager, self).end()
		self.icons = None

		AddStatusIcon.unsubscribe(self.on_add_icon_message)
		HoverInstancesChanged.unsubscribe(self.on_hover_instances_changed)
		RemoveStatusIcon.unsubscribe(self.on_remove_icon_message)
		WorldObjectDeleted.unsubscribe(self.on_worldobject_deleted_message)

	def on_add_icon_message(self, message):
		"""This is called by the message bus with AddStatusIcon messages"""
		assert isinstance(message, AddStatusIcon)
		icon_instance = message.icon.instance
		if not icon_instance in self.icons:
			self.icons[icon_instance] = []
		assert not message.icon in self.icons[icon_instance]
		self.icons[icon_instance].append(message.icon)
		# Sort, make sure highest icon is at top
		self.icons[icon_instance] = sorted(self.icons[icon_instance], key=StatusIcon.get_sorting_key(), reverse=True)
		# Now render the most important one
		self.__render_status(icon_instance, self.icons[icon_instance][0])

		if self.tooltip_instance is not None and self.tooltip_instance is icon_instance: # possibly have to update tooltip
			self.on_hover_instances_changed( HoverInstancesChanged(self, [self.tooltip_instance]) )

	def on_worldobject_deleted_message(self, message):
		assert isinstance(message, WorldObjectDeleted)
		# remove icon
		if message.worldobject in self.icons:
			self.remove_icon(message.worldobject)
		# remove icon tooltip
		if message.worldobject is self.tooltip_instance:
			self.on_hover_instances_changed( HoverInstancesChanged(self, []) )

	def on_remove_icon_message(self, message):
		"""Called by the MessageBus with RemoveStatusIcon messages."""
		assert isinstance(message, RemoveStatusIcon)
		icon_instance = message.instance
		if icon_instance in self.icons:
			for registered_icon in self.icons[icon_instance][:]:
				if message.icon_class is registered_icon.__class__:
					self.icons[icon_instance].remove(registered_icon)
					if not self.icons[icon_instance]:
						# No icon left for this building, remove it
						self.remove_icon(icon_instance)
					else:
						# Render next icon
						self.__render_status(icon_instance, self.icons[icon_instance][0])
					break

			if self.tooltip_instance is not None and self.tooltip_instance is icon_instance: # possibly have to update tooltip
				self.on_hover_instances_changed( HoverInstancesChanged(self, [self.tooltip_instance]) )

	def remove_icon(self, instance):
		""" Remove the icon.
		Also removes the entry in the icons-dictionary.
		"""
		super(StatusIconManager, self).remove_icon(self.get_renderer_group_name(instance))
		del self.icons[instance]

	def __render_status(self, instance, status):
		status_string = self.get_renderer_group_name(instance)
		loc = super(StatusIconManager, self).pre_render_icon(instance, status_string)

		# Let the status-icon render itself
		status.render(self.renderer, status_string, loc)

	def on_hover_instances_changed(self, msg):
		"""Check if we need to display a tooltip"""
		instances = msg.instances

		# only those that have icons
		instances = (i for i in instances if i in self.icons)
		# and belong to the player
		instances = [i for i in instances if
		             hasattr(i, "owner" ) and
		             hasattr(i.owner, "is_local_player") and
		             i.owner.is_local_player]

		if not instances:
			# hide
			self.tooltip_instance = None
			self.tooltip_icon.hide_tooltip()
		else:
			# get tooltip text, set, position and show
			self.tooltip_instance = instances[0] # pick any (usually ordered by fife)

			icons_of_instance = self.icons[self.tooltip_instance]
			icon = max(icons_of_instance, key=StatusIcon.get_sorting_key())

			self.tooltip_icon.helptext = icon.helptext

			pos = NavigationTool.last_event_pos
			self.tooltip_icon.position_tooltip( (pos.x, pos.y) )
			self.tooltip_icon.show_tooltip()
