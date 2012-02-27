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

	The first argument in each message is always a reference to the sender,
	additional expected arguments are defined on the class-level attribute `arguments`,
	these will be stored on the instance.
	"""
	arguments = tuple()

	def __init__(self, sender, *args):
		self.sender = sender
		if len(self.arguments) != len(args):
			raise Exception('Unexpected number of arguments. Expected %d, received %d' % (
				len(self.arguments), len(args)))

		for arg, value in zip(self.arguments, args):
			setattr(self, arg, value)


class AddStatusIcon(Message):
	arguments = ('icon', )

class RemoveStatusIcon(Message):
	arguments = (
		'instance',		# the instance from which to remove the icon
		'icon_class'	# class object of the icon that is to be removed
	)

class RemoveAllStatusIcons(Message):
	arguments = ('instance', )

class SettlerUpdate(Message):
	arguments = ('level', )

class SettlerInhabitantsChanged(Message):
	"""Class to signal that the number of inhabitants in a settler building
	have changed."""
	arguments = ('change', )

class ResourceBarResize(Message):
	"""Signals a change in resource bar size (not slot changes, but number of slot changes)"""
	pass

class UpgradePermissionsChanged(Message):
	"""In a settlement."""
	pass

class SettlementRangeChanged(Message):
	"""Called on grow and perhaps shrink once that's implemented. Used by buildingtool.
	Send by a Settlement."""
	arguments = (
		'changed_tiles', # Actual tile objects
	)

class WorldObjectDeleted(Message):
	"""Called when a world object is being deleted.
	Currently emitted in the process of destruction, i.e. you aren't guaranteed to be able to access any attributes. (Feel free to change the implementation if you need this).
	"""
	arguments = ('worldid', )
