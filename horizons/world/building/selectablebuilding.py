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

from horizons.constants import GFX
from horizons.util import decorators

class SelectableBuilding(object):
	range_applies_only_on_island = True
	selection_color = (255, 255, 0)
	_selected_tiles = [] # tiles that are selected. used for clean deselect.
	is_selectable = True

	def select(self, reset_cam=False):
		"""Runs necessary steps to select the building."""
		self.set_selection_outline()
		if reset_cam:
			self.session.view.center(*self.position.origin.to_tuple())
		renderer = self.session.view.renderer['InstanceRenderer']
		self._do_select(renderer, self.position, self.session.world, self.settlement)
		self._is_selected = True

	def set_selection_outline(self):
		"""Only set the selection outline.
		Useful when it has been removed by some kind of interference"""
		renderer = self.session.view.renderer['InstanceRenderer']
		renderer.addOutlined(self._instance, self.selection_color[0], self.selection_color[1],
		                     self.selection_color[2], GFX.BUILDING_OUTLINE_WIDTH,
		                     GFX.BUILDING_OUTLINE_THRESHOLD)

	def deselect(self):
		"""Runs neccassary steps to deselect the building.
		Only deselects if this building has been selected."""
		if not hasattr(self, "_is_selected") or not self._is_selected:
			return # only deselect selected buildings (simplifies other code)
		self._is_selected = False
		renderer = self.session.view.renderer['InstanceRenderer']
		renderer.removeOutlined(self._instance)
		renderer.removeAllColored()

	def remove(self):
		super(SelectableBuilding, self).remove()
		#TODO move this as a listener
		if self in self.session.selected_instances:
			self.session.selected_instances.remove(self)
		if self.owner == self.session.world.player:
			self.deselect()

	@classmethod
	def select_building(cls, session, position, settlement):
		"""Select a hypothecial instance of this class. Use Case: Buildingtool.
		Only works on a subclass of BuildingClass, since it requires certain class attributes.
		@param session: Session instance
		@param position: Position of building, usually Rect
		@param settlement: Settlement instance the building belongs to"""
		renderer = session.view.renderer['InstanceRenderer']

		"""
		import cProfile as profile
		import tempfile
		outfilename = tempfile.mkstemp(text = True)[1]
		print 'profile to ', outfilename
		profile.runctx( "cls._do_select(renderer, position, session.world, settlement)", globals(), locals(), outfilename)
		"""
		cls._do_select(renderer, position, session.world, settlement)

	@classmethod
	def deselect_building(cls, session):
		"""@see select_building,
		@return list of tiles that were deselected."""
		remove_colored = session.view.renderer['InstanceRenderer'].removeColored
		for tile in cls._selected_tiles:
			remove_colored(tile._instance)
			if tile.object is not None:
				remove_colored(tile.object._instance)
		selected_tiles = cls._selected_tiles
		cls._selected_tiles = []
		return selected_tiles

	@classmethod
	def _do_select(cls, renderer, position, world, settlement):
		if cls.range_applies_only_on_island:
			island = world.get_island(position.origin)
			if island is None:
				return # preview isn't on island, and therefore invalid

			ground_holder = None # use settlement or island as tile provider (prefer settlement, since it contains fewer tiles)
			if settlement is None:
				ground_holder = island
			else:
				ground_holder = settlement

			for tile in ground_holder.get_tiles_in_radius(position, cls.radius, include_self=False):
				try:
					if ( 'constructible' in tile.classes or 'coastline' in tile.classes ):
						cls._add_selected_tile(tile, position, renderer)
				except AttributeError:
					pass # no tile or no object on tile
		else:
			# we have to color water too
			for tile in world.get_tiles_in_radius(position.center(), cls.radius):
				try:
					if settlement is None or tile.settlement is None or tile.settlement == settlement:
						cls._add_selected_tile(tile, position, renderer)
				except AttributeError:
					pass # no tile or no object on tile


	@classmethod
	def _add_selected_tile(cls, tile, position, renderer):
		cls._selected_tiles.append(tile)
		renderer.addColored(tile._instance, *cls.selection_color)
		# Add color to objects on tht tiles
		renderer.addColored(tile.object._instance, *cls.selection_color)



decorators.bind_all(SelectableBuilding)