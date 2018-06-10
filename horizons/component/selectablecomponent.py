# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

import copy
import itertools
import operator

from fife import fife

import horizons.globals
from horizons.component import Component
from horizons.constants import GFX, LAYERS, RES
from horizons.util.shapes import RadiusRect


class SelectableComponent(Component):
	"""Stuff you can select.
	Has to be subdivided in buildings and units, which is further specialized to ships.

	Provides:
	show_menu(): shows tabs
	select(): highlight instance visually
	deselect(): inverse of select

	show_menu() and select() are frequently used in combination.

	The definitions must contain type, tabs and enemy_tabs.
	"""

	NAME = "selectablecomponent"

	@classmethod
	def get_instance(cls, arguments):
		# this can't be class variable because the classes aren't defined when
		# it would be parsed
		TYPES = {'building': SelectableBuildingComponent,
		         'unit': SelectableUnitComponent,
		         'ship': SelectableShipComponent,
		         'fisher': SelectableFisherComponent, }
		arguments = copy.copy(arguments)
		t = arguments.pop('type')
		return TYPES[t](**arguments)

	def __init__(self, tabs, enemy_tabs, active_tab=None):
		super().__init__()
		# resolve tab
		from horizons.gui.tabs import resolve_tab
		self.tabs = list(map(resolve_tab, tabs))
		self.enemy_tabs = list(map(resolve_tab, enemy_tabs))
		self.active_tab = resolve_tab(active_tab) if active_tab is not None else None
		self._selected = False

	def show_menu(self, jump_to_tabclass=None):
		"""Shows tabwidget tabs of this instance.

		Opens the first such tab unless jump_to_tabclass specifies otherwise.
		@param jump_to_tabclass: open the first tab that is a subclass to this parameter
		"""
		from horizons.gui.tabs import TabWidget
		tablist = None
		if self.instance.owner is not None and self.instance.owner.is_local_player:
			tablist = self.tabs
		else: # this is an enemy instance with respect to the local player
			tablist = self.enemy_tabs

		if not tablist:
			return

		tabclasses = [tabclass for tabclass in tablist if tabclass.shown_for(self.instance)]
		try:
			active_tab_index = tabclasses.index(self.active_tab)
		except ValueError:
			active_tab_index = None
		tabs = [tabclass(self.instance) for tabclass in tabclasses]
		tabwidget = TabWidget(self.session.ingame_gui, tabs=tabs, active_tab=active_tab_index)

		if jump_to_tabclass:
			for i, tab in enumerate(tabs):
				if isinstance(tab, jump_to_tabclass):
					tabwidget.show_tab(i)
					break
		self.session.ingame_gui.show_menu(tabwidget)

	def select(self, reset_cam=False):
		self._selected = True
		if reset_cam:
			self.session.view.center(*self.instance.position.center.to_tuple())

	def deselect(self):
		self._selected = False

	@property
	def selected(self):
		return self._selected

	def remove(self):
		if self.instance in self.session.selected_instances:
			self.session.selected_instances.remove(self.instance)
		for group in self.session.selection_groups:
			group.discard(self)
		if self._selected:
			self.deselect()
		super().remove()


class SelectableBuildingComponent(SelectableComponent):

	selection_color = (255, 255, 32, 192)

	# these smell like instance attributes, but sometimes have to be used in non-instance
	# contexts (e.g. building tool).
	class ListHolder:
		def __init__(self):
			self.l = []

	# read/write on class variables is somewhat borked in python, so
	_selected_tiles = ListHolder() # tiles that are selected. used for clean deselect.
	_selected_fake_tiles = ListHolder() # fake tiles create over ocean to select (can't select ocean directly)

	@classmethod
	def reset(cls):
		"""Called on session end to get rid of static data and init variables"""
		cls._selected_tiles.l = []
		cls._selected_fake_tiles.l = []

	def __init__(self, tabs, enemy_tabs, active_tab=None, range_applies_only_on_island=True):
		super().__init__(tabs, enemy_tabs, active_tab=active_tab)
		self.range_applies_only_on_island = range_applies_only_on_island

	def initialize(self):
		# check for related buildings (defined in db, not yaml)
		related_buildings = self.session.db.get_related_building_ids_for_menu(self.instance.id)
		if related_buildings:
			from horizons.gui.tabs import BuildRelatedTab
			self.tabs += (BuildRelatedTab,)

	def load(self, db, worldid):
		self.initialize()

	def select(self, reset_cam=False):
		"""Runs necessary steps to select the building."""
		super().select(reset_cam)
		self.set_selection_outline()
		if self.instance.owner is None or not self.instance.owner.is_local_player:
			return # don't show enemy ranges
		renderer = self.session.view.renderer['InstanceRenderer']
		self._do_select(renderer, self.instance.position, self.session.world,
		                self.instance.settlement, self.instance.radius, self.range_applies_only_on_island)

	def set_selection_outline(self):
		"""Only set the selection outline.
		Useful when it has been removed by some kind of interference"""
		renderer = self.session.view.renderer['InstanceRenderer']
		renderer.addOutlined(self.instance._instance, self.selection_color[0], self.selection_color[1],
		                     self.selection_color[2], GFX.BUILDING_OUTLINE_WIDTH,
		                     GFX.BUILDING_OUTLINE_THRESHOLD)

	def deselect(self):
		"""Runs neccassary steps to deselect the building.
		Only deselects if this building has been selected."""
		if self._selected:
			super().deselect()
			renderer = self.session.view.renderer['InstanceRenderer']
			renderer.removeOutlined(self.instance._instance)
			renderer.removeAllColored()
			for fake_tile in self.__class__._selected_fake_tiles.l:
				self.session.view.layers[LAYERS.FIELDS].deleteInstance(fake_tile)
			self.__class__._selected_fake_tiles.l = []

	@classmethod
	def select_building(cls, session, position, settlement,
	                    radius, range_applies_only_on_island):
		"""Select a hypothecial instance of this class. Use Case: Buildingtool.
		Only works on a subclass of BuildingClass, since it requires certain class attributes.
		@param session: Session instance
		@param position: Position of building, usually Rect
		@param settlement: Settlement instance the building belongs to"""
		renderer = session.view.renderer['InstanceRenderer']

		cls._do_select(renderer, position, session.world, settlement,
		               radius, range_applies_only_on_island)

	@classmethod
	def deselect_building(cls, session):
		"""@see select_building
		Used by building tool, allows incremental updates
		@return list of tiles that were deselected (only normal tiles, no fake tiles)"""
		remove_colored = session.view.renderer['InstanceRenderer'].removeColored
		for tile in cls._selected_tiles.l:
			remove_colored(tile._instance)
			if tile.object is not None:
				remove_colored(tile.object._instance)
		selected_tiles = cls._selected_tiles.l
		cls._selected_tiles.l = []
		for fake_tile in cls._selected_fake_tiles.l:
			session.view.layers[LAYERS.FIELDS].deleteInstance(fake_tile)
		cls._selected_fake_tiles.l = []
		return selected_tiles

	@classmethod
	def select_many(cls, buildings, renderer):
		"""Same as calling select() on many instances, but way faster.
		Limited functionality, only use on real buildings of a settlement."""
		if not buildings:
			return [] # that is not many

		selected_tiles = []

		# group buildings per settlement and treat them separately
		# they cannot share tiles, and we can then just access the settlements ground map
		buildings_sorted = sorted(buildings, key=operator.attrgetter('settlement'))
		for settlement, buildings in itertools.groupby(
				buildings_sorted, operator.attrgetter('settlement')):
			# resolve operator
			buildings = list(buildings)

			for building in buildings:
				building.get_component(SelectableComponent).set_selection_outline()

			coords = {coord for
			          building in buildings for
			          coord in building.position.get_radius_coordinates(building.radius, include_self=True)}

			for coord in coords:
				tile = settlement.ground_map.get(coord)
				if tile:
					if ('constructible' in tile.classes or 'coastline' in tile.classes):
						cls._add_selected_tile(tile, renderer)
						selected_tiles.append(tile)
		return selected_tiles

	@classmethod
	def _do_select(cls, renderer, position, world, settlement,
	               radius, range_applies_only_on_island):
		island = world.get_island(position.origin)
		if island is None:
			return # preview isn't on island, and therefore invalid

		if range_applies_only_on_island:
			ground_holder = None # use settlement or island as tile provider (prefer settlement, since it contains fewer tiles)
			if settlement is None:
				ground_holder = island
			else:
				ground_holder = settlement

			for tile in ground_holder.get_tiles_in_radius(position, radius, include_self=False):
				if 'constructible' in tile.classes or 'coastline' in tile.classes:
					if settlement is None and tile.settlement is not None:
						# trying to build a warehouse and the tile is already owned by another player.
						continue
					cls._add_selected_tile(tile, renderer)
		else:
			# we have to color water too
			# since water tiles are huge, create fake tiles and color them
			cls._init_fake_tile()

			layer = world.session.view.layers[LAYERS.FIELDS]
			# color island or fake tile
			for tup in position.get_radius_coordinates(radius):
				tile = island.get_tile_tuple(tup)
				if tile is not None:
					cls._add_selected_tile(tile, renderer)
				else: # need extra tile
					cls._add_fake_tile(tup[0], tup[1], layer, renderer)

	@classmethod
	def _init_fake_tile(cls):
		"""Sets the _fake_tile_obj class variable with a ready to use fife object.

		To create a new fake tile, use _add_fake_tile()."""
		# use fixed SelectableBuildingComponent here, to make sure subclasses also read the same variable
		if not hasattr(SelectableBuildingComponent, "_fake_tile_obj"):
			# create object to create instances from
			fake_tile_obj = horizons.globals.fife.engine.getModel().createObject('fake_tile_obj', 'ground')
			SelectableBuildingComponent._fake_tile_obj = fake_tile_obj
			fife.ObjectVisual.create(SelectableBuildingComponent._fake_tile_obj)

			img_path = 'content/gfx/fake_water.png'
			img = horizons.globals.fife.imagemanager.load(img_path)
			for rotation in [45, 135, 225, 315]:
				SelectableBuildingComponent._fake_tile_obj.get2dGfxVisual().addStaticImage(rotation, img.getHandle())

	@classmethod
	def _add_fake_tile(cls, x, y, layer, renderer):
		"""Adds a fake tile to the position. Requires 'cls._fake_tile_obj' to be set."""
		inst = layer.createInstance(SelectableBuildingComponent._fake_tile_obj,
	                                fife.ModelCoordinate(x, y, 0), "")
		fife.InstanceVisual.create(inst)
		cls._selected_fake_tiles.l.append(inst)
		renderer.addColored(inst, *cls.selection_color)

	@classmethod
	def _add_selected_tile(cls, tile, renderer, remember=True):
		"""
		@param remember: whether to keep track of this tile. Set to False on recolorings.
		"""
		if remember:
			cls._selected_tiles.l.append(tile)
		renderer.addColored(tile._instance, *cls.selection_color)
		# Add color to objects on the tiles
		obj = tile.object
		if obj is not None:
			renderer.addColored(obj._instance, *cls.selection_color)


class SelectableUnitComponent(SelectableComponent):

	def select(self, reset_cam=False):
		"""Runs necessary steps to select the unit."""
		super().select(reset_cam)
		self.session.view.renderer['InstanceRenderer'].addOutlined(self.instance._instance, 255, 255, 255, GFX.UNIT_OUTLINE_WIDTH, GFX.UNIT_OUTLINE_THRESHOLD)
		self.instance.draw_health()
		self.session.view.add_change_listener(self.instance.draw_health)

	def deselect(self):
		"""Runs necessary steps to deselect the unit."""
		if not self._selected:
			return
		super().deselect()
		self.session.view.renderer['InstanceRenderer'].removeOutlined(self.instance._instance)
		self.instance.draw_health(remove_only=True)
		# this is necessary to make deselect idempotent
		self.session.view.discard_change_listener(self.instance.draw_health)


class SelectableShipComponent(SelectableUnitComponent):

	def select(self, reset_cam=False):
		"""Runs necessary steps to select the ship."""
		super().select(reset_cam=reset_cam)

		# add a buoy at the ship's target if the player owns the ship
		if self.instance.owner.is_local_player:
			self.instance._update_buoy()
			self.session.ingame_gui.minimap.show_unit_path(self.instance)

	def deselect(self):
		"""Runs necessary steps to deselect the ship."""
		if self._selected:
			super().deselect()
			self.instance._update_buoy(remove_only=True)


class SelectableFisherComponent(SelectableBuildingComponent):
	"""Class used to highlight the radius of a fisher. Highlights only the fishing
	grounds."""

	@classmethod
	def _do_select(cls, renderer, position, world, settlement, radius,
	               range_applies_only_on_island):
		# No super, we don't want to color the ground
		cls._init_fake_tile()
		layer = world.session.view.layers[LAYERS.FIELDS]
		for fish_deposit in world.get_providers_in_range(RadiusRect(position, radius), res=RES.FISH):
			#renderer.addColored(fish_deposit._instance, *cls.selection_color)
			#cls._selected_tiles.l.append(fish_deposit)
			for pos in fish_deposit.position:
				cls._add_fake_tile(pos.x, pos.y, layer, renderer)
