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

import weakref
import logging
import horizons.globals

from horizons.entities import Entities
from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.util.shapes import Point
from horizons.util.worldobject import WorldObject
from horizons.command.building import Build
from horizons.component.selectablecomponent import SelectableComponent
from horizons.constants import BUILDINGS, GFX
from horizons.gui.util import load_uh_widget

class PreviewHandler(object):
	log = logging.getLogger("gui.buildingtool")

	buildable_color = (255, 255, 255)
	not_buildable_color = (255, 0, 0)
	related_building_color = (0, 192, 0)
	related_building_outline = (16, 228, 16, 2)
	nearby_objects_radius = 4

	# archive the last roads built, for possible user notification
	_last_road_built = []

	send_hover_instances_update = False
	
	gui = None # share gui between instances
	
	def highlight_buildable(self, tiles_to_check=None, new_buildings=True):
		"""Highlights all buildable tiles and select buildings that are inversely related in order to show their range.
		@param tiles_to_check: list of tiles to check for coloring.
		@param new_buildings: Set to true if you have set tiles_to_check and there are new buildings. An internal structure for optimisation will be amended."""
		self._build_logic.highlight_buildable(self, tiles_to_check)

		# Also distinguish inversely related buildings (lumberjack for tree).
		# Highlight their range at all times.
		# (There is another similar highlight, but it only marks building when
		# the current build preview is in its range)
		related = self.session.db.get_inverse_related_building_ids(self._class.id)

		# If the current buildings has related buildings, also show other buildings
		# of this class. You usually don't want overlapping ranges of e.g. lumberjacks.
		if self._class.id in self.session.db.get_buildings_with_related_buildings() and \
		   self._class.id != BUILDINGS.RESIDENTIAL:
			# TODO: generalize settler class exclusion, e.g. when refactoring it into components

			related = related + [self._class.id] # don't += on retrieved data from db

		related = frozenset(related)

		renderer = self.session.view.renderer['InstanceRenderer']
		if tiles_to_check is None or new_buildings: # first run, check all
			buildings_to_select = [ buildings_to_select
			                        for settlement in self.session.world.settlements
			                        if settlement.owner.is_local_player
			                        for bid in related
			                        for buildings_to_select in settlement.buildings_by_id[bid] ]

			tiles = self.selectable_comp.select_many(buildings_to_select, renderer)
			self._related_buildings_selected_tiles = frozenset(tiles)
		else: # we don't need to check all
			# duplicates filtered later
			buildings_to_select = [ tile.object for tile in tiles_to_check if
			                        tile.object is not None and tile.object.id in related ]
			for tile in tiles_to_check:
				# check if we need to recolor the tiles
				if tile in self._related_buildings_selected_tiles:
					self.selectable_comp._add_selected_tile(tile, renderer, remember=False)

		for building in buildings_to_select:
			self._related_buildings.add(building)
		
	def draw_gui(self):
		if not hasattr(self, "action_set"):
			level = self.session.world.player.settler_level if \
				not hasattr(self._class, "default_level_on_build") else \
				self._class.default_level_on_build
			action_set = self._class.get_random_action_set(level=level)
		action_sets = ActionSetLoader.get_sets()
		for action_option in ['idle', 'idle_full', 'abcd']:
			if action_option in action_sets[action_set]:
				action = action_option
				break
		else: # If no idle, idle_full or abcd animation found, use the first you find
			action = action_sets[action_set].keys()[0]
		rotation = (self.rotation + int(self.session.view.cam.getRotation()) - 45) % 360
		image = sorted(action_sets[action_set][action][rotation].keys())[0]
		if GFX.USE_ATLASES:
			# Make sure the preview is loaded
			horizons.globals.fife.animationloader.load_image(image, action_set, action, rotation)
		building_icon = self.gui.findChild(name='building')
		loaded_image = horizons.globals.fife.imagemanager.load(image)
		building_icon.image = fife.GuiImage(loaded_image)
		width = loaded_image.getWidth()
		# TODO: Remove hardcoded 220
		max_width = 220
		if width > max_width:
			height = loaded_image.getHeight()
			size = (max_width, (height * max_width) // width)
			building_icon.max_size = building_icon.min_size = building_icon.size = size
		# TODO: Remove hardcoded 70
		gui_x, gui_y = self.__class__.gui.size
		icon_x, icon_y = building_icon.size
		building_icon.position = (gui_x // 2 - icon_x // 2,
		                          gui_y // 2 - icon_y // 2 - 70)
		self.__class__.gui.adaptLayout()
		
	def load_gui(self):
		if self.__class__.gui is None:
			self.__class__.gui = load_uh_widget("place_building.xml")
			top_bar = self.__class__.gui.findChild(name='top_bar')
			top_bar.position = ((self.__class__.gui.size[0] // 2) - (top_bar.size[0] // 2) - 16, 50)
			self.__class__.gui.position_technique = "right-1:top+157"
		self.__class__.gui.mapEvents( { "rotate_left" : self.rotate_left,
		                                "rotate_right": self.rotate_right } )
		# set translated building name in gui
		self.__class__.gui.findChild(name='headline').text = _('Build {building}').format(building=_(self._class.name))
		self.__class__.gui.findChild(name='running_costs').text = unicode(self._class.running_costs)
		head_box = self.__class__.gui.findChild(name='head_box')
		head_box.adaptLayout() # recalculates size of new content
		# calculate and set new center
		new_x = max(25, (self.__class__.gui.size[0] // 2) - (head_box.size[0] // 2))
		head_box.position = (new_x, head_box.position[1])
		head_box.adaptLayout()
		self.draw_gui()
		
	def preview_build(self, point1, point2, force=False):
		"""Display buildings as preview if build requirements are met"""
		#self.session.view.renderer['InstanceRenderer'].removeAllColored()
		self.log.debug("BuildingTool: preview build at %s, %s", point1, point2)
		new_buildings = self._class.check_build_line(self.session, point1, point2,
		                                             rotation=self.rotation, ship=self.ship)
		# optimisation: If only one building is in the preview and the position hasn't changed
		# => don't preview. Otherwise the preview is redrawn on every mouse move
		if not force and len(new_buildings) == len(self.buildings) == 1 and \
		   new_buildings[0] == self.buildings[0]:
			return # we don't want to redo the preview

		# remove old fife instances and coloring
		self._remove_building_instances()

		# get new ones
		self.buildings = new_buildings
		# resize list of action set ids to new buildings
		self.buildings_action_set_ids = self.buildings_action_set_ids + ([None] * (len(self.buildings) - len(self.buildings_action_set_ids)))
		self.buildings_action_set_ids = self.buildings_action_set_ids[ : len(self.buildings) ]
		# delete old infos
		self.buildings_fife_instances.clear()
		self.buildings_missing_resources.clear()

		settlement = None # init here so we can access it below loop
		needed_resources = {}
		# check if the buildings are buildable and color them appropriately
		for i, building in enumerate(self.buildings):
			# get gfx for the building
			# workaround for buildings like settler, that don't use the current level of
			# the player, but always start at a certain lvl
			level = self._class.get_initial_level(self.session.world.player)

			if self._class.id == BUILDINGS.TREE and not building.buildable:
				continue # Tree/ironmine that is not buildable, don't preview
			else:
				fife_instance, action_set_id = \
					self._class.getInstance(self.session, building.position.origin.x,
								            building.position.origin.y, rotation=building.rotation,
								            action=building.action, level=level,
								            action_set_id=self.buildings_action_set_ids[i])
				self.buildings_fife_instances[building] = fife_instance
				# remember action sets per order of occurrence
				# (this is far from good when building lines, but suffices for our purposes, which is mostly single build)
				self.buildings_action_set_ids[i] = action_set_id

			settlement = self.session.world.get_settlement(building.position.origin)
			if settlement is not None and settlement.owner != self.session.world.player:
				settlement = None # no fraternising with the enemy, else there would be peace

			if self._class.id != BUILDINGS.WAREHOUSE:
				# Player shouldn't be allowed to build in this case, else it can trigger
				# a new_settlement notification
				if settlement is None:
					building.buildable = False


			# check required resources
			(enough_res, missing_res) = Build.check_resources(needed_resources, self._class.costs,
			                                                  self.session.world.player, [settlement, self.ship])
			if building.buildable and not enough_res:
					# make building red
					self.renderer.addColored(self.buildings_fife_instances[building],
					                         *self.not_buildable_color)
					building.buildable = False
					# set missing info for gui
					self.buildings_missing_resources[building] = missing_res

			# color this instance with fancy stuff according to buildability

			# this order determines highlight priority
			# draw ordinary ranges first, then later color related buildings (they are more important)
			self._make_surrounding_transparent(building)
			self._color_preview_building(building)
			if building.buildable:
				self._draw_preview_building_range(building, settlement)
			self._highlight_related_buildings_in_range(building, settlement)
			self._highlight_inversely_related_buildings(building, settlement)

		self.session.ingame_gui.resource_overview.set_construction_mode(
			self.ship if self.ship is not None else settlement,
		  needed_resources
		)
		self._add_listeners(self.ship if self.ship is not None else settlement)
		
	def _color_preview_building(self, building):
		"""Draw fancy stuff for build preview
		@param building: return value from buildable, _BuildPosition
		"""
		if building.buildable:
			# Tile might still have not buildable color -> remove it
			self.renderer.removeColored(self.buildings_fife_instances[building])
			self.renderer.addOutlined(self.buildings_fife_instances[building],
			                          self.buildable_color[0], self.buildable_color[1],
			                          self.buildable_color[2], GFX.BUILDING_OUTLINE_WIDTH,
			                          GFX.BUILDING_OUTLINE_THRESHOLD)

		else: # not buildable
			# must remove other highlight, fife does not support both
			self.renderer.removeOutlined(self.buildings_fife_instances[building])
			self.renderer.addColored(self.buildings_fife_instances[building],
			                         *self.not_buildable_color)
									 
	def _draw_preview_building_range(self, building, settlement):
		"""Color the range as if the building was selected"""
		radius_only_on_island = True
		if hasattr(self.selectable_comp, 'range_applies_only_on_island'):
			radius_only_on_island = self.selectable_comp.range_applies_only_on_island

		self.selectable_comp.select_building(self.session, building.position, settlement,
		                                     self._class.radius, radius_only_on_island)
											 
	def _highlight_related_buildings_in_range(self, building, settlement):
		"""Highlight directly related buildings (tree for lumberjacks) that are in range of the build preview"""
		if settlement is not None:
			related = frozenset(self.session.db.get_related_building_ids(self._class.id))
			for tile in settlement.get_tiles_in_radius(building.position, self._class.radius, include_self=True):
				obj = tile.object
				if (obj is not None) and (obj.id in related) and (obj not in self._highlighted_buildings):
					self._highlighted_buildings.add( (obj, False) ) # False: was_selected, see _restore_highlighted_buildings
					# currently same code as highlight_related_buildings
					inst = obj.fife_instance
					self.renderer.addOutlined(inst, *self.related_building_outline)
					self.renderer.addColored(inst, *self.related_building_color)

	def _make_surrounding_transparent(self, building):
		"""Makes the surrounding of building_position transparent and hide buildings
		that are built upon (tearset)"""
		world_contains = self.session.world.map_dimensions.contains_without_border
		get_tile = self.session.world.get_tile
		for coord in building.position.get_radius_coordinates(self.nearby_objects_radius, include_self=True):
			p = Point(*coord)
			if not world_contains(p):
				continue
			tile = get_tile(p)
			if tile.object is not None and tile.object.buildable_upon:
				inst = tile.object.fife_instance
				inst.get2dGfxVisual().setTransparency(BUILDINGS.TRANSPARENCY_VALUE)
				self._transparencified_instances.add(weakref.ref(inst))

		for to_tear_worldid in building.tearset:
			inst = WorldObject.get_object_by_id(to_tear_worldid).fife_instance
			inst.get2dGfxVisual().setTransparency(255) # full transparency = hidden
			self._transparencified_instances.add(weakref.ref(inst))

	def _highlight_inversely_related_buildings(self, building, settlement):
		"""Point out buildings that are inversly relevant (e.g. lumberjacks when building trees)
		This is triggered on each preview change and highlights only those in range"""
		# tuple for fast lookup with few elements
		ids = tuple(self.session.db.get_inverse_related_building_ids(self._class.id))
		if settlement is None or not ids: # nothing is related
			return

		radii = dict( [ (bid, Entities.buildings[bid].radius) for bid in ids ] )
		max_radius = max(radii.itervalues())

		for tile in settlement.get_tiles_in_radius(building.position, max_radius, include_self=True):
			if tile.object is not None and tile.object.id in ids:
				related_building = tile.object
				# check if it was actually this one's radius
				if building.position.distance( (tile.x, tile.y) ) <= \
				   Entities.buildings[related_building.id].radius:
					# found one
					if related_building in self._highlighted_buildings:
						continue

					self._highlighted_buildings.add( (related_building, True) ) # True: was_selected, see _restore_highlighted_buildings
					# currently same code as coloring normal related buildings (_color_preview_build())
					inst = related_building.fife_instance
					self.renderer.addOutlined(inst, *self.related_building_outline)
					self.renderer.addColored(inst, *self.related_building_color)
					
	def _restore_highlighted_buildings(self):
		"""Inverse of highlight_related_buildings"""
		# assemble list of all tiles that have are occupied by now restored buildings
		# (if but one of them is in the range of something, the whole building
		# might need to be colored as "in range")
		modified_tiles = []
		for (building, was_selected) in self._highlighted_buildings:
			inst = building.fife_instance
			self.renderer.removeColored(inst)
			# related buildings are highlighted, restore it
			if was_selected:
				self.renderer.addColored(inst, *self.selectable_comp.selection_color)
			self.renderer.removeOutlined(inst)
			modified_tiles.extend(
			  ( self.session.world.get_tile(point) for point in building.position )
			)
		self._highlighted_buildings.clear()
		self.highlight_buildable(modified_tiles)
		
	def _remove_building_instances(self):
		"""Deletes fife instances of buildings"""

		try:
			self._class.get_component_template(SelectableComponent)
		except KeyError:
			pass
		else:
			deselected_tiles = self.selectable_comp.deselect_building(self.session)
			# redraw buildables (removal of selection might have tampered with it)
			self.highlight_buildable(deselected_tiles)

		self._restore_transparencified_instances()
		self._restore_highlighted_buildings()
		for building in self._related_buildings:
			# restore selection, removeOutline can destroy it
			building.get_component(SelectableComponent).set_selection_outline()
		for fife_instance in self.buildings_fife_instances.itervalues():
			layer = fife_instance.getLocationRef().getLayer()
			# layer might not exist, happens for some reason after a build
			if layer is not None:
				layer.deleteInstance(fife_instance)
		self.buildings_fife_instances = {}

	def _restore_transparencified_instances(self):
		"""Removes transparency"""
		for inst_weakref in self._transparencified_instances:
			fife_instance = inst_weakref()
			if fife_instance:
				# remove transparency only if trees aren't supposed to be transparent as default
				if not hasattr(fife_instance, "keep_translucency") or not fife_instance.keep_translucency:
					fife_instance.get2dGfxVisual().setTransparency(0)
				else:
					# restore regular translucency value, can also be different
					fife_instance.get2dGfxVisual().setTransparency( BUILDINGS.TRANSPARENCY_VALUE )
		self._transparencified_instances.clear()

	def _remove_coloring(self):
		"""Removes coloring from tiles, that indicate that the tile is buildable
		as well as all highlights. Called when building mode is finished."""
		for building in self._related_buildings:
			building.get_component(SelectableComponent).deselect()
		self.renderer.removeAllOutlines()
		self.renderer.removeAllColored()
		
	def _color_buildable_tile(self, tile):
		self._buildable_tiles.add(tile) # it's a set, so duplicates are handled
		self.renderer.addColored(tile._instance, *self.buildable_color)
