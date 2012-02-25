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

class Message(object):
	"""Message class for the MessageBus. Every Message that is supposed to be
	send through the MessageBus should subclass this base class, to ensure proper
	setting of base attributes.
	"""

	def __init__(self, sender):
		self.sender = sender


class AddStatusIcon(Message):

	def __init__(self, sender, icon):
		super(AddStatusIcon, self).__init__(sender)
		self.icon = icon

class RemoveStatusIcon(Message):

	def __init__(self, sender, instance, icon_class):
		"""@param instance: the instance from which to remove the icon
		@param icon_class: class object of the icon that is to be removed"""
		super(RemoveStatusIcon, self).__init__(sender)
		self.instance = instance
		self.icon_class = icon_class

class RemoveAllStatusIcons(Message):

	def __init__(self, sender, instance):
		super(RemoveAllStatusIcons, self).__init__(sender)
		self.instance = instance

class SettlerUpdate(Message):

	def __init__(self, sender, level):
		super(SettlerUpdate, self).__init__(sender)
		self.level = level

class SettlerInhabitantsChanged(Message):
	"""Class to signal that the number of inhabitants in a settler building
	have changed."""
	def __init__(self, sender, change):
		super(SettlerInhabitantsChanged, self).__init__(sender)
		self.change = change

class ResourceBarResize(Message):
	"""Signals a change in resource bar size (not slot changes, but number of slot changes)"""
	pass

class UpgradePermissionsChanged(Message):
	"""In a settlement."""
	pass

class SettlementRangeChanged(Message):
	"""Called on grow and perhaps shrink once that's implemented. Used by buildingtool.
	@param sender: Settlement
	@param changed_tiles: Actual tile objects"""
	def __init__(self, sender, changed_tiles):
		super(SettlementRangeChanged, self).__init__(sender)
		self.changed_tiles = changed_tiles

class WorldObjectDeleted(Message):
	"""Called when a world object is being deleted.
	Currently emitted in the process of destruction, i.e. you aren't guaranteed to be able to access any attributes. (Feel free to change the implementation if you need this).
	"""
	def __init__(self, sender, worldid):
		super(WorldObjectDeleted, self).__init__(sender)
		self.worldid = worldid
