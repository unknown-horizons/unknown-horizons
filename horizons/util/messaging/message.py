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

	def __init__(self, sender, icon):
		super(RemoveStatusIcon, self).__init__(sender)
		self.icon = icon

class RemoveAllStatusIcons(Message):

	def __init__(self, sender, instance):
		super(RemoveAllStatusIcons, self).__init__(sender)
		self.instance = instance