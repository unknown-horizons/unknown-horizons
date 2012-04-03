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
import copy

import horizons.main

from horizons.world.component import Component
from horizons.util import decorators
from horizons.constants import GFX, LAYERS

class SelectableComponent(Component):
	"""Stuff you can select.
	Has to be subdivided in buildings and units, which is further specialised to ships.

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
		TYPES = { 'building' : SelectableBuildingComponent,
		          'unit'     : SelectableUnitComponent,
		          'ship'     : SelectableShipComponent }
		arguments = copy.copy(arguments)
		t = arguments.pop('type')
		return TYPES[ t ]( **arguments )

	def __init__(self, tabs, enemy_tabs):
		super(SelectableComponent, self).__init__()
		# resolve tab
		from horizons.gui import tabs as tab_classes
		resolve_tab = lambda tab_class_name : getattr(tab_classes, tab_class_name)
		self.tabs = map(resolve_tab, tabs)
		self.enemy_tabs = map(resolve_tab, enemy_tabs)
		self._selected = False

	def show_menu(self, jump_to_tabclass=None):
		"""Shows tabs from self.__class__.tabs, if there are any.
		@param jump_to_tabclass: open the first tab that is a subclass to this parameter
		"""
		from horizons.gui.tabs import TabWidget
		tablist = None
		if self.instance.owner is not None and self.instance.owner.is_local_player:
			tablist = self.tabs
		else: # this is an enemy instance with respect to the local player
			tablist = self.enemy_tabs

		if tablist:
			tabs = [ tabclass(self.instance) for tabclass in tablist if
			         tabclass.shown_for(self.instance) ]
			tabwidget = TabWidget(self.session.ingame_gui, tabs=tabs)

			if jump_to_tabclass:
				for i, tab in enumerate(tabs):
					if isinstance(tab, jump_to_tabclass):
						tabwidget._show_tab(i)
						break

			self.session.ingame_gui.show_menu( tabwidget )

	def select(self, reset_cam=False):
		self._selected = True
		if reset_cam:
			self.session.view.center(*self.instance.position.center().to_tuple())

	def deselect(self):
		self._selected = False

	@property
	def selected(self):
		return self._selected

	def remove(self):
		if self.instance in self.session.selected_instances:
			self.session.selected_instances.remove(self.instance)
		if self._selected:
			self.deselect()
		super(SelectableComponent, self).remove()


class SelectableBuildingComponent(SelectableComponent):

	selection_color = (255, 255, 100)

	# these smell like instance attributes, but sometimes have to be used in non-instance
	# contexts (e.g. building tool).
	class ListHolder(object):
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


	def __init__(self, tabs, enemy_tabs, range_applies_on_island=True, range_applies_on_water=False):
		super(SelectableBuildingComponent, self).__init__(tabs, enemy_tabs)

		self.range_applies_on_island = range_applies_on_island
		self.range_applies_on_water = range_applies_on_water

	def initialize(self):
		# check for related buildings (defined in db, not yaml)
		related_buildings = self.session.db.get_related_building_ids_for_menu(self.instance.id)
		if len(related_buildings) > 0:
			from horizons.gui.tabs import BuildRelatedTab
			self.tabs += (BuildRelatedTab,)

	def load(self, db, worldid):
		self.initialize()

	def select(self, reset_cam=False):
		"""Runs necessary steps to select the building."""
		super(SelectableBuildingComponent, self).select(reset_cam)
		self.set_selection_outline()
		if self.instance.owner is None or not self.instance.owner.is_local_player:
			return # don't show enemy ranges
		renderer = self.session.view.renderer['InstanceRenderer']
		self._do_select(renderer, self.instance.position, self.session.world,
		                self.instance.settlement, self.instance.radius, self.range_applies_on_island, self.range_applies_on_water )

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
			super(SelectableBuildingComponent, self).deselect()
			renderer = self.session.view.renderer['InstanceRenderer']
			renderer.removeOutlined(self.instance._instance)
			SelectableBuildingComponent.deselect_building(self.session)

	@classmethod
	def select_building(cls, session, position, settlement,
	                    radius, range_applies_on_island, range_applies_on_water):
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
		c = "cls._do_select(renderer, position, session.world, settlement)"
		profile.runctx(c, globals(), locals(), outfilename)
		"""
		cls._do_select(renderer, position, session.world, settlement,
		               radius, range_applies_on_island, range_applies_on_water)

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
	def select_many_buildings(cls, buildings, renderer, ground_tiles = True, water_tiles = True):
		"""Same as calling select() on many instances, but way faster.
		Selects many buildings along with ranges, used when user
		drags selection box
		@param buildings: iterable of buildings to select
		@param renderer: instance of renderer
		@param ground_tiles: should this function work on ground range buildings?
		@param water_tiles: should this function work on water range buildings?
		"""
		if not buildings:
			return []# that is not many

		# component from building[0] is needed to get island as ground holder
		comp0 = buildings[0].get_component(SelectableBuildingComponent)
		world = comp0.session.world
		island = world.get_island(comp0.instance.position.origin)

		# buildings which range has to be shown on water
		water_buildings = []

		# buildings which range has to be shown on ground
		ground_buildings = []

		if ground_tiles:
			for building in buildings:
				comp = building.get_component(SelectableBuildingComponent)
				comp.set_selection_outline()
				comp._selected = True
				if comp.range_applies_on_island:
					ground_buildings.append(building)
				if comp.range_applies_on_water:
					water_buildings.append(building)
	
			coords = set( coord for \
			              building in ground_buildings for \
			              coord in building.position.get_radius_coordinates(building.radius, include_self=True) )
	
			for coord in coords:
				tile = island.ground_map.get(coord)
				if tile:
					if ( 'constructible' in tile.classes or 'coastline' in tile.classes ):
						cls._add_selected_tile(tile, renderer)
	
		# code below is for drawing fake range tiles on water
		if water_tiles and water_buildings:
			# create object to create instances from
			SelectableBuildingComponent._create_fake_tile_obj()

			layer = world.session.view.layers[LAYERS.FIELDS]

			# draw fake range tiles on water for each building
			for building in water_buildings:
				comp = building.get_component(SelectableComponent)
				position = comp.instance.position
				radius = comp.instance.radius
				island = world.get_island(position.origin)
				
				SelectableBuildingComponent._select_fake_water_tiles(position, island, radius, layer, renderer)
		return ground_buildings + water_buildings
		
	@classmethod
	def _create_fake_tile_obj(cls):
		# create object to create instances from
		if not hasattr(cls, "_fake_tile_obj"):
			cls._fake_tile_obj = horizons.main.fife.engine.getModel().createObject('fake_tile_obj', 'ground')
			fife.ObjectVisual.create(cls._fake_tile_obj)
	
			img_path = 'content/gfx/base/fake_water.png'
			img = horizons.main.fife.imagemanager.load(img_path)
			for rotation in [45, 135, 225, 315]:
				cls._fake_tile_obj.get2dGfxVisual().addStaticImage(rotation, img.getHandle())

	@classmethod
	def _select_fake_water_tiles(cls, position, island, radius, layer, renderer):
		for tup in position.get_radius_coordinates(radius):
			tile = island.get_tile_tuple(tup)
			if tile is None:
				inst = layer.createInstance(cls._fake_tile_obj,
				                            fife.ModelCoordinate(tup[0], tup[1], 0), "")
				fife.InstanceVisual.create(inst)
				cls._selected_fake_tiles.l.append(inst)
				renderer.addColored(inst, *cls.selection_color)

#	@classmethod
#	def select_many(cls, buildings, renderer):
#		"""Same as calling select() on many instances, but way faster.
#		Limited functionality, only use on real buildings of a settlement."""
#		if not buildings:
#			return [] # that is not many
#		settlement = buildings[0].settlement
#
#		for building in buildings:
#			building.get_component(SelectableComponent).set_selection_outline()
#
#		coords = set( coord for \
#		              building in buildings for \
#		              coord in building.position.get_radius_coordinates(building.radius, include_self=True) )
#
#		selected_tiles = []
#		for coord in coords:
#			tile = settlement.ground_map.get(coord)
#			if tile:
#				if ( 'constructible' in tile.classes or 'coastline' in tile.classes ):
#					cls._add_selected_tile(tile, renderer)
#					selected_tiles.append(tile)
#		return selected_tiles

	@classmethod
	def _do_select(cls, renderer, position, world, settlement,
	               radius, range_applies_on_island, range_applies_on_water):
		island = world.get_island(position.origin)
		if island is None:
			return # preview isn't on island, and therefore invalid

		if range_applies_on_island:
			ground_holder = None # use settlement or island as tile provider (prefer settlement, since it contains fewer tiles)
			if settlement is None:
				ground_holder = island
			else:
				ground_holder = settlement

			for tile in ground_holder.get_tiles_in_radius(position, radius, include_self=False):
				if ( 'constructible' in tile.classes or 'coastline' in tile.classes ):
					cls._add_selected_tile(tile, renderer)

		if range_applies_on_water:
			# we have to color water too
			# since water tiles are huge, create fake tiles and color them
			SelectableBuildingComponent._create_fake_tile_obj()
			layer = world.session.view.layers[LAYERS.FIELDS]
			# color fake tiles
			SelectableBuildingComponent._select_fake_water_tiles(position, island, radius, layer, renderer)
			
	@classmethod
	def _add_selected_tile(cls, tile, renderer, remember=True):
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
		super(SelectableUnitComponent, self).select(reset_cam)
		self.session.view.renderer['InstanceRenderer'].addOutlined(self.instance._instance, 255, 255, 255, GFX.UNIT_OUTLINE_WIDTH, GFX.UNIT_OUTLINE_THRESHOLD)
		self.instance.draw_health()
		self.session.view.add_change_listener(self.instance.draw_health)

	def deselect(self):
		"""Runs necessary steps to deselect the unit."""
		if self._selected:
			super(SelectableUnitComponent, self).deselect()
			self.session.view.renderer['InstanceRenderer'].removeOutlined(self.instance._instance)
			self.instance.draw_health(remove_only=True)
			# this is necessary to make deselect idempotent
			if self.session.view.has_change_listener(self.instance.draw_health):
				self.session.view.remove_change_listener(self.instance.draw_health)

class SelectableShipComponent(SelectableUnitComponent):

	def select(self, reset_cam=False):
		"""Runs necessary steps to select the ship."""
		super(SelectableShipComponent, self).select(reset_cam=reset_cam)

		# add a buoy at the ship's target if the player owns the ship
		if self.instance.owner.is_local_player:
			self.instance._update_buoy()
			self.session.ingame_gui.minimap.show_unit_path(self.instance)

	def deselect(self):
		"""Runs necessary steps to deselect the ship."""
		if self._selected:
			super(SelectableShipComponent, self).deselect()
			self.instance._update_buoy(remove_only=True)

decorators.bind_all(SelectableBuildingComponent)
decorators.bind_all(SelectableShipComponent)
decorators.bind_all(SelectableUnitComponent)
