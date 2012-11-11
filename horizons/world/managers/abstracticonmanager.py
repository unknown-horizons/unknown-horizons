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

from fife import fife

class AbstractIconManager(object):
	"""Abstract Manager-Class for all IconManagers"""

	def __init__(self, renderer, layer):
		"""
		@param renderer: Renderer used to render the icons
		@param layer: map layer, needed to place icon
		"""
		self.layer = layer
		self.renderer = renderer

	def end(self):
		self.renderer = None

	def pre_render_icon(self, instance, group):
		""" This has to be called before __render_icon.
		It calculates the position of the icon
		"""

		# Clear all icons
		self.renderer.removeAll(group)
		pos = instance.position

		# Calculate position for icon
		loc = fife.Location(self.layer)
		coord = fife.ExactModelCoordinate(pos.origin.x + pos.width / 4.0,
		                                  pos.origin.y + pos.height / 4.0)
		loc.setExactLayerCoordinates(coord)
		return loc

	def remove_icon(self, group):
		"""Removes the icon"""
		self.renderer.removeAll(group)
