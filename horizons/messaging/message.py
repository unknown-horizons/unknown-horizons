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

from horizons.messaging.messagebus import MessageBus


class Message(object):
	"""Message class for the MessageBus. Every Message that is supposed to be
	send through the MessageBus has to subclass this base class, to ensure proper
	setting of base attributes and inheriting the interface.

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
			MessageBus().subscribe_locally(cls, sender, callback)
		else:
			MessageBus().subscribe_globally(cls, callback)

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
			MessageBus().unsubscribe_locally(cls, sender, callback)
		else:
			MessageBus().unsubscribe_globally(cls, callback)

	@classmethod
	def discard(cls, callback):
		"""Similar to `Message.unsubscribe`, but does not raise an error if the
		callback has not been registered before.
		"""
		MessageBus().discard_globally(cls, callback)

	@classmethod
	def broadcast(cls, *args):
		"""Send a message that is initialized with `args`.

		The first argument is always a sender, the number of arguments has to be
		N + 1, with N beeing the number of arguments defined on the message class.

		Example:

			>>> class Foo(Message):
			... 	arguments = ('a', 'b', )

			>>> Foo.broadcast('sender', 1, 2)
		"""
		MessageBus().broadcast(cls(*args))


class AddStatusIcon(Message):
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
	arguments = ('worldobject', 'worldid', )


class NewPlayerSettlementHovered(Message):
	"""Sent when the mouse hovers over a different settlement than before,
	and it belongs to the local player or is None."""
	arguments = ('settlement', )

class HoverSettlementChanged(Message):
	"""Sent when hovering over any different settlement, or no settlement."""
	arguments = ('settlement', )

class NewSettlement(Message):
	"""Sent when a new settlement is created"""
	arguments = ('settlement', )

class HoverInstancesChanged(Message):
	"""Sent when hovering over a different set of instances.
	Not sent on every mouse move but with a bit of delay to be able to do more extensive
	computation without risk of delays."""
	arguments = ('instances', )

class NewDisaster(Message):
	"""Sent when a building is affected by a disaster."""
	arguments = ('building', 'disaster_class', )

class TabWidgetChanged(Message):
	"""Sent when the ingamegui displays a different set of tabs, i.e. the tabwidget is exchanged.
	The tabs are not necessarily different from the old ones."""
	pass

class GuiAction(Message):
	"""Sent on events pychan classifies as "action" """
	pass

class ResourceProduced(Message):
	"""Sent when a production building finished the production of a resource """
	arguments = ('produced_resources', )