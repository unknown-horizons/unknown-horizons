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

from fife import fife

import horizons.main

from horizons.world.component import Component
from horizons.util import decorators
from horizons.constants import GFX, LAYERS

class SelectableComponent(Component):
	"""Stuff you can select"""

	NAME = "selectablecomponent"

	@classmethod
	def get_instance(cls, arguments):
		# this can't be class variable because the classes aren't defined when
		# it would be parsed
		TYPES = { 'building' : SelectableBuildingComponent,
		          'unit'     : SelectableUnitComponent,
		          'ship'     : SelectableShipComponent }
		t = arguments.pop('type')
		return TYPES[ t ]( arguments )

class SelectableBuildingComponent(SelectableComponent):

	selection_color = (255, 255, 0)

	# these smell like instance attributes, but sometimes have to be used in non-instance
	# contexts (e.g. building tool).
	_selected_tiles = [] # tiles that are selected. used for clean deselect.
	_selected_fake_tiles = []

	def __init__(self, range_applies_only_on_island=True):
		super(SelectableComponent, self).__init__()
		self.range_applies_only_on_island = range_applies_only_on_island

	def select(self, reset_cam=False):
		"""Runs necessary steps to select the building."""
		self.set_selection_outline()
		if reset_cam:
			self.instance.session.view.center(*self.position.origin.to_tuple())
		renderer = self.instance.session.view.renderer['InstanceRenderer']
		self._do_select(renderer, self.position, self.instance.session.world, self.settlement)
		self._is_selected = True

	def set_selection_outline(self):
		"""Only set the selection outline.
		Useful when it has been removed by some kind of interference"""
		renderer = self.instance.session.view.renderer['InstanceRenderer']
		renderer.addOutlined(self._instance, self.selection_color[0], self.selection_color[1],
		                     self.selection_color[2], GFX.BUILDING_OUTLINE_WIDTH,
		                     GFX.BUILDING_OUTLINE_THRESHOLD)

	def deselect(self):
		"""Runs neccassary steps to deselect the building.
		Only deselects if this building has been selected."""
		if not hasattr(self, "_is_selected") or not self._is_selected:
			return # only deselect selected buildings (simplifies other code)
		self._is_selected = False
		renderer = self.instance.session.view.renderer['InstanceRenderer']
		renderer.removeOutlined(self._instance)
		renderer.removeAllColored()
		for fake_tile in self.__class__._selected_fake_tiles:
			self.instance.session.view.layers[LAYERS.FIELDS].deleteInstance(fake_tile)
		self.__class__._selected_fake_tiles = []

	def remove(self):
		#TODO move this as a listener
		if self in self.instance.session.selected_instances:
			self.instance.session.selected_instances.remove(self)
		if self.owner == self.instance.session.world.player:
			self.deselect()
		super(SelectableBuildingComponent, self).remove()

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
		"""@see select_building
		Used by building tool, allows incremental updates
		@return list of tiles that were deselected."""
		remove_colored = session.view.renderer['InstanceRenderer'].removeColored
		for tile in cls._selected_tiles:
			remove_colored(tile._instance)
			if tile.object is not None:
				remove_colored(tile.object._instance)
		selected_tiles = cls._selected_tiles
		cls._selected_tiles = []
		for fake_tile in cls._selected_fake_tiles:
			session.view.layers[LAYERS.FIELDS].deleteInstance(fake_tile)
		cls._selected_fake_tiles = []
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
						cls._add_selected_tile(tile, renderer)
				except AttributeError:
					pass # no tile or no object on tile
		else:
			# we have to color water too
			# since water tiles are huge, create fake tiles and color them

			if not hasattr(cls, "_fake_tile_obj"):
				# create object to create instances from
				cls._fake_tile_obj = horizons.main.fife.engine.getModel().createObject('fake_tile_obj', 'ground')
				fife.ObjectVisual.create(cls._fake_tile_obj)

				img_path = 'content/gfx/base/water/fake_water.png'
				img = horizons.main.fife.imagemanager.load(img_path)
				for rotation in [45, 135, 225, 315]:
					cls._fake_tile_obj.get2dGfxVisual().addStaticImage(rotation, img.getHandle())

			layer = world.session.view.layers[LAYERS.FIELDS]
			island = world.get_island(position.origin)
			# color island or fake tile
			for tup in position.get_radius_coordinates(cls.radius):
				tile = island.get_tile_tuple(tup)
				if tile is not None:
					try:
						cls._add_selected_tile(tile, renderer)
					except AttributeError:
						pass # no tile or no object on tile
				else: # need extra tile
					inst = layer.createInstance(cls._fake_tile_obj,
					                            fife.ModelCoordinate(tup[0], tup[1], 0), "")
					fife.InstanceVisual.create(inst)

					cls._selected_fake_tiles.append(inst)
					renderer.addColored(inst, *cls.selection_color)

	@classmethod
	def _add_selected_tile(cls, tile, renderer):
		cls._selected_tiles.append(tile)
		renderer.addColored(tile._instance, *cls.selection_color)
		# Add color to objects on tht tiles
		renderer.addColored(tile.object._instance, *cls.selection_color)


class SelectableUnitComponent(SelectableComponent):

	def select(self, reset_cam=False):
		"""Runs necessary steps to select the unit."""
		self.instance.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, GFX.UNIT_OUTLINE_WIDTH, GFX.UNIT_OUTLINE_THRESHOLD)
		self.instance.draw_health()

	def deselect(self):
		"""Runs necessary steps to deselect the unit."""
		self.instance.session.view.renderer['InstanceRenderer'].removeOutlined(self._instance)
		self.instance.session.view.renderer['GenericRenderer'].removeAll("health_" + str(self.worldid))
		# this is necessary to make deselect idempotent
		if self.instance.session.view.has_change_listener(self.instance.draw_health):
			self.instance.session.view.remove_change_listener(self.instance.draw_health)


class SelectableShipComponent(SelectableUnitComponent):

	def select(self, reset_cam=False):
		"""Runs necessary steps to select the ship."""
		self.instance._selected = True
		super(SelectableShipComponent, self).select(reset_cam=reset_cam)

		# add a buoy at the ship's target if the player owns the ship
		if self.instance.session.world.player == self.owner:
			self.instance._update_buoy()

		if self.owner is self.instance.session.world.player:
			self.instance.session.ingame_gui.minimap.show_unit_path(self)

	def deselect(self):
		"""Runs necessary steps to deselect the ship."""
		self.instance._selected = False
		super(SelectableShipComponent, self).deselect()
		self.instance.session.view.renderer['GenericRenderer'].removeAll("buoy_" + str(self.worldid))



decorators.bind_all(SelectableBuildingComponent)
decorators.bind_all(SelectableShipComponent)
decorators.bind_all(SelectableUnitComponent)