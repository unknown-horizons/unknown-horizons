# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from typing import Tuple

from horizons.messaging.messagebus import MessageBus
from horizons.messaging.queuingmessagebus import QueuingMessageBus


class Message:
	"""Message class for the MessageBus. Every Message that is supposed to be
	sent through the MessageBus has to subclass this base class, to ensure proper
	setting of base attributes and inheriting the interface.

	The first argument in each message is always a reference to the sender,
	additional expected arguments are defined on the class-level attribute `arguments`,
	these will be stored on the instance.
	"""
	arguments = tuple() # type: Tuple[str, ...]
	bus = MessageBus

	def __init__(self, sender, *args):
		self.sender = sender
		if len(self.arguments) != len(args):
			raise Exception('Unexpected number of arguments. Expected {:d}, received {:d}'.format(
				len(self.arguments), len(args)))

		for arg, value in zip(self.arguments, args):
			setattr(self, arg, value)

	@classmethod
	def subscribe(cls, callback, sender=None):
		"""Register a callback to be called whenever a message of this type is send.

		callback - Callable that receives an instance of a message as only argument.

		sender	-	If specified, the callback receives only messages that originated
					from sender. By default, all messages are received.

		Example:

			>>> def cb(msg):
			... 	print 'Received', msg

			>>> MessageClass.subscribe(cb)	# Global
			>>> MessageClass.subscribe(cb, sender=foo) # Specific sender
		"""
		if sender:
			cls.bus().subscribe_locally(cls, sender, callback)
		else:
			cls.bus().subscribe_globally(cls, callback)

	@classmethod
	def unsubscribe(cls, callback, sender=None):
		"""Stop your subscription of this message type for the specified callback.

		callback -	Callable that receives an instance of a message as only argument.
					The same you've been using with `Message.subscribe`.

		sender	-	If specified, the subscription will only be stopped for messages
					from this sender. By default, all subscriptions are ended.

		Note: There has to be a subscription, otherwise an error will be raised.

		Example:

			>>> MessageClass.subscribe(cb)
			>>> MessageClass.broadcast('sender')
			message received
			>>> MessageClass.unsubscribe(cb)
			>>> MessageClass.broadcast('sender')
		"""
		if sender:
			cls.bus().unsubscribe_locally(cls, sender, callback)
		else:
			cls.bus().unsubscribe_globally(cls, callback)

	@classmethod
	def discard(cls, callback, sender=None):
		"""Similar to `Message.unsubscribe`, but does not raise an error if the
		callback has not been registered before.
		"""
		if sender:
			cls.bus().discard_locally(cls, sender, callback)
		else:
			cls.bus().discard_globally(cls, callback)

	@classmethod
	def broadcast(cls, *args):
		"""Send a message that is initialized with `args`.

		The first argument is always a sender, the number of arguments has to be
		N + 1, with N being the number of arguments defined on the message class.

		Example:

			>>> class Foo(Message):
			... 	arguments = ('a', 'b', )

			>>> Foo.broadcast('sender', 1, 2)
		"""
		cls.bus().broadcast(cls(*args))


class QueuingMessage(Message):
	"""QueuingMessage class for the QueuingMessageBus. Every Message that is supposed to be
	sent through the QueuingMessageBus has to subclass this subclass.
	"""
	bus = QueuingMessageBus

	@classmethod
	def clear(cls, *args):
		"""Empty the message queue for this Message class
		"""
		cls.bus().clear(cls)

	@classmethod
	def queue_len(cls, *args):
		"""Get the length the message queue for this Message class
		"""
		return cls.bus().queue_len(cls)


class AddStatusIcon(QueuingMessage):
	arguments = ('icon', )


class RemoveStatusIcon(Message):
	arguments = (
		'instance',		# the instance from which to remove the icon
		'icon_class'	# class object of the icon that is to be removed
	)


class SettlerUpdate(Message):
	"""Sent when the level of a settler building changes. Message includes the new
	level and the change (+1/-1).
	"""
	arguments = ('level', 'change', )


class PlayerLevelUpgrade(Message):
	"""Sent when the settler level of a player increases."""
	arguments = ('level', 'building', )


class SettlerInhabitantsChanged(Message):
	"""Class to signal that the number of inhabitants in a settler building
	have changed."""
	arguments = ('change', )


class ResourceBarResize(Message):
	"""Signals a change in resource bar size (not slot changes, but number of slot changes)."""
	pass


class UpgradePermissionsChanged(Message):
	"""In a settlement."""
	pass


class SettlementRangeChanged(Message):
	"""Called on grow and perhaps shrink once that's implemented. Used by buildingtool.
	Sent by a Settlement."""
	arguments = (
		'changed_tiles', # Actual tile objects
	)


class WorldObjectDeleted(Message):
	"""Called when a world object is being deleted.
	Currently emitted in the process of destruction, i.e. you aren't guaranteed
	to be able to access any attributes.
	(Feel free to change the implementation if you need this).
	"""
	arguments = ('worldobject', 'worldid', )


class ShipDestroyed(Message):
	"""Sent just when a ship is destroyed."""
	pass


class NewPlayerSettlementHovered(Message):
	"""Sent when the mouse hovers over a different settlement than before,
	and it belongs to the local player or is None."""
	arguments = ('settlement', )


class HoverSettlementChanged(Message):
	"""Sent when hovering over any different settlement, or no settlement."""
	arguments = ('settlement', )


class NewSettlement(Message):
	"""Sent when a new settlement is created."""
	arguments = ('settlement', 'warehouse_position', )


class HoverInstancesChanged(Message):
	"""Sent when hovering over a different set of instances.
	Not sent on every mouse move but with a bit of delay to be able to do more extensive
	computation without risk of delays."""
	arguments = ('instances', )


class NewDisaster(Message):
	"""Sent when a building is affected by a disaster."""
	arguments = ('building', 'disaster_class', 'disaster')


class TabWidgetChanged(Message):
	"""Sent when the ingamegui displays a different set of tabs, i.e. the tabwidget is exchanged.
	The tabs are not necessarily different from the old ones."""
	pass


class GuiAction(Message):
	"""Sent on events pychan classifies as "action"."""
	pass


class GuiCancelAction(Message):
	"""Sent on events that originate from the cancelButton."""
	pass


class GuiHover(Message):
	"""Sent on mouseEntered events"""
	pass


class ResourceProduced(Message):
	"""Sent when a production building finished the production of a resource."""
	arguments = ('caller', 'produced_resources', )


class InstanceInventoryUpdated(Message):
	"""Message sent whenever an inventory of any instance is updated.

	This message is sent by StorageComponent but sender is the instance!
	"""
	arguments = ('inventory', )


class SettlementInventoryUpdated(Message):
	"""Message sent whenever a settlement's inventory is updated."""
	pass


class PlayerInventoryUpdated(Message):
	"""Message sent whenever a player's inventory is updated."""
	pass


class LanguageChanged(Message):
	"""Sent when the language has changed."""
	pass


class SpeedChanged(Message):
	"""Sent when the ingame speed has changed."""
	arguments = ('old', 'new', )


class SettingChanged(Message):
	"""Sent when a setting is changed in the dialog."""
	arguments = ('setting_name', 'old_value', 'new_value', )


class MineEmpty(Message):
	"""Sent when there are no more resources left in a mine."""
	arguments = ('mine', )


class LoadingProgress(Message):
	"""Sent when loading screen is updated with a new progress hint."""
	arguments = ('stage', )


class ZoomChanged(Message):
	"""Sent when map zoom has changed."""
	arguments = ('zoom', )


class ActionChanged(Message):
	"""Sent when a ConcreteObject changed its action"""
	arguments = ('action', )
