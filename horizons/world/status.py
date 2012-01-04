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

import horizons.main

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
	def __init__(self, priority, icon):
		"""
		@param priority: integer
		@param icon: fife identifier for animations or icons. Must be supported by either
		             the animationloader or the imagemanager.
		"""
		self.priority = priority
		self.icon = icon

	@staticmethod
	def get_sorting_key():
		"""Use like this:
		sorted(mylist, key=mylist.get_sorting_key())
		or
		mylist.sort(key=mylist.get_sorting_key())
		"""
		return operator.attrgetter("priority")

	def render(self, renderer, key, renderernode):
		try: # to load an animation
			anim = horizons.main.fife.animationloader.loadResource( self.icon )
			renderer.addAnimation( key, renderernode, anim )
		except ValueError as e:
			img = horizons.main.fife.imagemanager.load( self.icon )
			renderer.addImage( key, renderernode, img )

	def __cmp__(self, other):
		return cmp(self.__class__, other.__class__)

	def __str__(self):
		return str(self.__class__) + "(prio:%s,icon:%s)" % (self.priority, self.icon)


class SettlerUnhappyStatus(StatusIcon):
	# threshold is the inhabitants decrease level
	def __init__(self):
		super(SettlerUnhappyStatus, self).__init__( 1700, "content/gui/icons/templates/happiness/sad.png")

class InventoryFullStatus(StatusIcon):
	def __init__(self, reslist):
		"""
		@param reslist: list of integers describing the resources
		"""
		super(InventoryFullStatus, self).__init__( 1200, "as_buoy0+idle+45" )
		self.reslist = reslist

class ProductivityLowStatus(StatusIcon):
	"""Terminology: productivity = capacity utilisation"""
	threshold = 0.25 # display when productivity lower than this
	def __init__(self):
		super(ProductivityLowStatus, self).__init__( 400, "as_buoy0+idle+45" )

class DecommissionedStatus(StatusIcon):
	"""Terminology: productiviy = capacity utilisation"""
	def __init__(self):
		super(DecommissionedStatus, self).__init__( 800, "as_buoy0+idle+45" )

