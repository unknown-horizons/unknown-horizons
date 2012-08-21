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

import operator

"""Classes used for StatusIcon.

Code design note:
The conditions for the statuses could also have been placed here,
for more modularity and flexiblity.
This way, we'd need to touch the objects' privates sometimes though,
and we'd lose some direct interaction flexiblity. Therefore, the objects
now contain all the logic, this module just covers the data.

Priority:
[   0-1000[: low
[1000-2000[: medium
[2000-3000[: high
Keep the numbers unique to avoid confusion when sorting.
"""
class StatusIcon(object):
	# integer
	priority = None
	# fife identifier for animations or icons. Must be supported by either the animationloader
	# or the imagemanager. (i.e. either file path or something like "as_buoy0+idle+45")
	icon = None
	_helptext = ""

	def __init__(self, instance):
		"""
		@param instance: the instance the icon is to be attached to
		"""
		self.instance = instance

	@staticmethod
	def get_sorting_key():
		"""Use like this:
		sorted(mylist, key=mylist.get_sorting_key())
		or
		mylist.sort(key=mylist.get_sorting_key())
		"""
		return operator.attrgetter("priority")

	@property
	def helptext(self):
		return _(self._helptext)

	def __cmp__(self, other):
		return cmp(self.__class__, other.__class__)

	def __str__(self):
		return str(self.__class__) + "(prio:%s,icon:%s)" % (self.priority, self.icon)


class FireStatusIcon(StatusIcon):
	""" Fire disaster """
	priority = 3000
	icon = 'as_on_fire+idle+45'
	_helptext = _(u"This building is on fire!")


class SettlerUnhappyStatus(StatusIcon):
	# threshold is the inhabitants decrease level
	priority = 1700
	icon = 'as_attention_please+idle+45'
	_helptext = _(u"These residents are unhappy.")


class InventoryFullStatus(StatusIcon):
	priority = 1200
	icon = 'as_inventory_full+idle+45'
	_helptext = _(u"The inventory of this building is full.")

	def __init__(self, instance, reslist):
		"""
		@param reslist: list of integers describing the resources
		"""
		super(InventoryFullStatus, self).__init__(instance)
		self.reslist = reslist


class ProductivityLowStatus(StatusIcon):
	"""Terminology: productivity = capacity utilisation"""
	threshold = 0.25 # display when productivity lower than this
	priority = 400
	icon = 'as_attention_please+idle+45'
	_helptext = _(u"This building has a very low productivity.")


class DecommissionedStatus(StatusIcon):
	priority = 800
	icon = 'as_decommissioned+idle+45'
	_helptext = _(u"This building is decomissioned.")


class PestilenceStatus(StatusIcon):
	priority = 2000
	icon = 'as_pestilence+idle+45'
	_helptext = _(u"The inhabitants of this building have the plague.")

