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

import logging
import random
import weakref
from typing import TYPE_CHECKING, List

from fife import fife

import horizons.globals
from horizons.command.building import Build
from horizons.command.sounds import PlaySound
from horizons.component.selectablecomponent import SelectableBuildingComponent, SelectableComponent
from horizons.constants import BUILDINGS, GFX
from horizons.entities import Entities
from horizons.extscheduler import ExtScheduler
from horizons.gui.mousetools.navigationtool import NavigationTool
from horizons.gui.util import load_uh_widget
from horizons.i18n import gettext as T
from horizons.messaging import (
	PlayerInventoryUpdated, SettlementInventoryUpdated, SettlementRangeChanged, WorldObjectDeleted)
from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.util.shapes import Point
from horizons.util.worldobject import WorldObject

if TYPE_CHECKING:
	from fife.extensions.pychan.widgets import Widget


class BuildingTool(NavigationTool):
	"""Represents a dangling tool after a building was selected from the list.
	Builder visualizes if and why a building can not be built under the cursor position.
	@param building: selected building type"
	@param ship: If building from a ship, restrict to range of ship

	The building tool has been under heavy development for several years, it's a collection
	of random artifacts that used to have a purpose once.

	Terminology:
	- Related buildings: Buildings lower in the hierarchy, needed by current building to operate (tree when building lumberjack)
	- Inversely related building: lumberjack for tree. Need to show its range to place building, it must be in range.
	- Building instances/fife instances: the image of a building, that is dragged around.

	Main features:
	- Display tab to the right, showing build preview icon and rotation button (draw_gui(), load_gui())
	- Show buildable ground (highlight buildable) as well as ranges of inversely related buildings
		- This also is called for tiles that need to be recolored, other highlights sometimes draw over
		  tiles, then this is called again to redo the original coloring.
	- Catch mouse events and handle preview on map:
		- Get tentative fife instances for buildings, draw them colored according to buildability
		- Check for resources missing for build
		- Making surrounding of preview transparent, so you see where you are building in a forest
		- Highlight related buildings, that are in range
		- Draw building range and highlight related buildings that are in range in this position (_color_preview_building)
	- Initiate actual build (do_build)
		- Clean up coloring, possibly end build mode
	- Several buildability logics, strategy pattern via self._build_logic.

	Interaction sequence:
	- Init, comprises mainly of gui init and highlight_buildable
	- Update, which is mainly controlled by preview_build
		- Update highlights related to build
			- Transparency
			- Inversely related buildings in range (highlight_related_buildings)
			- Related buildings in range (_color_preview_build)
		- Set new instances
		- During this time, don't touch anything set by highlight_buildable, or restore it later
	- End, possibly do_build and on_escape
	"""
	log = logging.getLogger("gui.buildingtool")

	buildable_color = (255, 255, 255)
	not_buildable_color = (255, 0, 0, 160)
	related_building_color = (0, 192, 0, 160)
	related_building_outline = (32, 192, 32, 3)
	nearby_objects_radius = 4

	# archive the last roads built, for possible user notification
	_last_road_built = [] # type: List[int]

	send_hover_instances_update = False

	# share gui between instances
	gui = None # type: Widget

	def __init__(self, session, building, ship=None, build_related=None):
		super().__init__(session)
		assert not (ship and build_related)
		self.renderer = self.session.view.renderer['InstanceRenderer']
		self.ship = ship
		self._class = building
		self.__init_selectable_component()
		self.buildings = [] # list of PossibleBuild objs
		self.buildings_action_set_ids = [] # list action set ids of list above
		self.buildings_fife_instances = {} # fife instances of possible builds
		self.buildings_missing_resources = {} # missing resources for possible builds
		self.rotation = 45 + random.randint(0, 3) * 90
		self.start_point, self.end_point = None, None
		self.last_change_listener = None
		self._transparencified_instances = set() # fife instances modified for transparency
		self._buildable_tiles = set() # tiles marked as buildable
		self._related_buildings = set() # buildings highlighted as related
		self._highlighted_buildings = set() # related buildings highlighted when preview is near it
		self._build_logic = None
		self._related_buildings_selected_tiles = frozenset() # highlights w.r.t. related buildings
		if self.ship is not None:
			self._build_logic = ShipBuildingToolLogic(ship)
		elif build_related is not None:
			self._build_logic = BuildRelatedBuildingToolLogic(self, weakref.ref(build_related))
		else:
			self._build_logic = SettlementBuildingToolLogic(self)

		self.load_gui()
		self.__class__.gui.show()
		self.session.ingame_gui.minimap_to_front()

		self.highlight_buildable()
		WorldObjectDeleted.subscribe(self._on_worldobject_deleted)

		SettlementInventoryUpdated.subscribe(self.update_preview)
		PlayerInventoryUpdated.subscribe(self.update_preview)

	def __init_selectable_component(self):
		self.selectable_comp = SelectableBuildingComponent
		try:
			template = self._class.get_component_template(SelectableComponent)
			self.selectable_comp = SelectableComponent.get_instance(template)
		except KeyError:
			pass

	def highlight_buildable(self, tiles_to_check=None, new_buildings=True):
		"""Highlights all buildable tiles and select buildings that are inversely related in order to show their range.
		@param tiles_to_check: list of tiles to check for coloring.
		@param new_buildings: Set to True if you have set tiles_to_check and there are new buildings. An internal structure for optimization will be amended."""
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
			buildings_to_select = [buildings_to_select
			                       for settlement in self.session.world.settlements
			                       if settlement.owner.is_local_player
			                       for bid in related
			                       for buildings_to_select in settlement.buildings_by_id[bid]]

			tiles = self.selectable_comp.select_many(buildings_to_select, renderer)
			self._related_buildings_selected_tiles = frozenset(tiles)
		else: # we don't need to check all
			# duplicates filtered later
			buildings_to_select = [tile.object for tile in tiles_to_check if
			                       tile.object is not None and tile.object.id in related]
			for tile in tiles_to_check:
				# check if we need to recolor the tiles
				if tile in self._related_buildings_selected_tiles:
					self.selectable_comp._add_selected_tile(tile, renderer, remember=False)

		for building in buildings_to_select:
			self._related_buildings.add(building)

	def _color_buildable_tile(self, tile):
		self._buildable_tiles.add(tile) # it's a set, so duplicates are handled
		self.renderer.addColored(tile._instance, *self.buildable_color)

	def remove(self):
		self.session.ingame_gui.resource_overview.close_construction_mode()
		WorldObjectDeleted.unsubscribe(self._on_worldobject_deleted)
		self._remove_listeners()
		self._remove_building_instances()
		self._remove_coloring()
		self._build_logic.remove(self.session)
		self._buildable_tiles = None
		self._transparencified_instances = None
		self._related_buildings_selected_tiles = None
		self._related_buildings = None
		self._highlighted_buildings = None
		self._build_logic = None
		self.buildings = None
		if self.__class__.gui is not None:
			self.__class__.gui.hide()
		ExtScheduler().rem_all_classinst_calls(self)
		SettlementInventoryUpdated.discard(self.update_preview)
		PlayerInventoryUpdated.discard(self.update_preview)
		super().remove()

	def _on_worldobject_deleted(self, message):
		# remove references to this object
		self._related_buildings.discard(message.sender)
		self._transparencified_instances = \
		  set(i for i in self._transparencified_instances if
		      i() is not None and int(i().getId()) != message.worldid)
		check_building = lambda b: b.worldid != message.worldid
		self._highlighted_buildings = set(tup for tup in self._highlighted_buildings if check_building(tup[0]))
		self._related_buildings = set(filter(check_building, self._related_buildings))

	def load_gui(self):
		if self.__class__.gui is None:
			self.__class__.gui = load_uh_widget("place_building.xml")
			self.__class__.gui.position_technique = "right-1:top+157"
		self.__class__.gui.mapEvents({"rotate_left": self.rotate_left,
		                              "rotate_right": self.rotate_right})
		# set translated building name in gui
		self.__class__.gui.findChild(name='headline').text = T('Build {building}').format(building=T(self._class.name))
		self.__class__.gui.findChild(name='running_costs').text = str(self._class.running_costs)
		head_box = self.__class__.gui.findChild(name='head_box')
		head_box.adaptLayout() # recalculates size of new content
		# calculate and set new center
		new_x = max(25, (self.__class__.gui.size[0] // 2) - (head_box.size[0] // 2))
		head_box.position = (new_x, head_box.position[1])
		head_box.adaptLayout()
		self.draw_gui()

	def draw_gui(self):
		if not hasattr(self, "action_set"):
			try:
				level = self._class.default_level_on_build
			except AttributeError:
				level = self.session.world.player.settler_level
			action_set = self._class.get_random_action_set(level=level)
		action_sets = ActionSetLoader.get_sets()
		for action_option in ['idle', 'idle_full', 'single', 'abcd']:
			if action_option in action_sets[action_set]:
				action = action_option
				break
		else: # If no idle, idle_full or abcd animation found, use the first you find
			action = list(action_sets[action_set].keys())[0]
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

	def preview_build(self, point1, point2, force=False):
		"""Display buildings as preview if build requirements are met"""
		#self.session.view.renderer['InstanceRenderer'].removeAllColored()
		self.log.debug("BuildingTool: preview build at %s, %s", point1, point2)
		new_buildings = self._class.check_build_line(self.session, point1, point2,
		                                             rotation=self.rotation, ship=self.ship)
		# optimization: If only one building is in the preview and the position hasn't changed
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
		self.buildings_action_set_ids = self.buildings_action_set_ids[: len(self.buildings)]
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
				settlement = None # no fraternizing with the enemy, else there would be peace

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
					self._highlighted_buildings.add((obj, False)) # False: was_selected, see _restore_highlighted_buildings
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
		"""Point out buildings that are inversely related (e.g. lumberjacks when building trees)
		This is triggered on each preview change and highlights only those in range"""
		# tuple for fast lookup with few elements
		ids = tuple(self.session.db.get_inverse_related_building_ids(self._class.id))
		if settlement is None or not ids: # nothing is related
			return

		radii = {bid: Entities.buildings[bid].radius for bid in ids}
		max_radius = max(radii.values())

		for tile in settlement.get_tiles_in_radius(building.position, max_radius, include_self=True):
			if tile.object is not None and tile.object.id in ids:
				related_building = tile.object
				# check if it was actually this one's radius
				if building.position.distance((tile.x, tile.y)) <= \
				   Entities.buildings[related_building.id].radius:
					# found one
					if related_building in self._highlighted_buildings:
						continue

					self._highlighted_buildings.add((related_building, True)) # True: was_selected, see _restore_highlighted_buildings
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
			  (self.session.world.get_tile(point) for point in building.position)
			)
		self._highlighted_buildings.clear()
		self.highlight_buildable(modified_tiles)

	def on_escape(self):
		self._build_logic.on_escape(self.session)
		if self.__class__.gui is not None:
			self.__class__.gui.hide()
		self.session.ingame_gui.set_cursor() # will call remove()

	def mouseMoved(self, evt):
		self.log.debug("BuildingTool mouseMoved")
		super().mouseMoved(evt)
		point = self.get_world_location(evt)
		if self.start_point != point:
			self.start_point = point
		self._check_update_preview(point)
		evt.consume()

	def mousePressed(self, evt):
		self.log.debug("BuildingTool mousePressed")
		if evt.isConsumedByWidgets():
			super().mousePressed(evt)
			return
		if evt.getButton() == fife.MouseEvent.RIGHT:
			self.on_escape()
		elif evt.getButton() == fife.MouseEvent.LEFT:
			pass
		else:
			super().mousePressed(evt)
			return
		evt.consume()

	def mouseDragged(self, evt):
		self.log.debug("BuildingTool mouseDragged")
		super().mouseDragged(evt)
		point = self.get_world_location(evt)
		if self.start_point is not None:
			self._check_update_preview(point)
		evt.consume()

	def mouseReleased(self, evt):
		"""Actually build."""
		self.log.debug("BuildingTool mouseReleased")
		if evt.isConsumedByWidgets():
			super().mouseReleased(evt)
		elif evt.getButton() == fife.MouseEvent.LEFT:
			point = self.get_world_location(evt)

			# check if position has changed with this event and update everything
			self._check_update_preview(point)

			# actually do the build
			changed_tiles = self.do_build()
			found_buildable = bool(changed_tiles)
			if found_buildable:
				PlaySound("build").execute(self.session, local=True)

			# HACK: users sometimes don't realize that roads can be dragged
			# check if 3 roads have been built within 1.2 seconds, and display
			# a hint in case
			if self._class.class_package == 'path':
				import time
				now = time.time()
				BuildingTool._last_road_built.append(now)
				if len(BuildingTool._last_road_built) > 2:
					if (now - BuildingTool._last_road_built[-3]) < 1.2:
						self.session.ingame_gui.message_widget.add('DRAG_ROADS_HINT')
						# don't display hint multiple times at the same build situation
						BuildingTool._last_road_built = []
					BuildingTool._last_road_built = BuildingTool._last_road_built[-3:]

			# check how to continue: either build again or escape
			shift = evt.isShiftPressed() or horizons.globals.fife.get_uh_setting('UninterruptedBuilding')
			if ((shift and not self._class.id == BUILDINGS.WAREHOUSE)
			    or not found_buildable
			    or self._class.class_package == 'path'):
				# build once more
				self._restore_transparencified_instances()
				self.highlight_buildable(changed_tiles)
				self.start_point = point
				self._build_logic.continue_build()
				self.preview_build(point, point)
			else:
				self.on_escape()
			evt.consume()
		elif evt.getButton() != fife.MouseEvent.RIGHT:
			super().mouseReleased(evt)

	def do_build(self):
		"""Actually builds the previews
		@return a set of tiles where buildings have really been built"""
		changed_tiles = set()

		# actually do the build and build preparations
		for i, building in enumerate(self.buildings):
			# remove fife instance, the building will create a new one.
			# Check if there is a matching fife instance, could be missing
			# in case of trees, which are hidden if not buildable
			if building in self.buildings_fife_instances:
				fife_instance = self.buildings_fife_instances.pop(building)
				self.renderer.removeColored(fife_instance)
				self.renderer.removeOutlined(fife_instance)
				fife_instance.getLocationRef().getLayer().deleteInstance(fife_instance)

			if building.buildable:
				island = self.session.world.get_island(building.position.origin)
				for position in building.position:
					tile = island.get_tile(position)
					if tile in self._buildable_tiles:
						# for some kind of buildabilities, not every coord of the
						# building is buildable (e.g. fisher: only coastline is marked
						# as buildable). For those tiles, that are not buildable,
						# we don't need to do anything.
						self._buildable_tiles.remove(tile)
						self.renderer.removeColored(tile._instance)
						changed_tiles.add(tile)
				self._remove_listeners() # Remove changelisteners for update_preview
				# create the command and execute it
				cmd = Build(building=self._class,
							x=building.position.origin.x,
							y=building.position.origin.y,
							rotation=building.rotation,
							island=island,
							settlement=self.session.world.get_settlement(building.position.origin),
							ship=self.ship,
							tearset=building.tearset,
							action_set_id=self.buildings_action_set_ids[i],
							)
				cmd.execute(self.session)
			else:
				if len(self.buildings) == 1: # only give messages for single bulds
					# first, buildable reasons such as grounds
					# second, resources

					if building.problem is not None:
						msg = building.problem[1]
						self.session.ingame_gui.message_widget.add_custom(
						  point=building.position.origin, messagetext=msg)

					# check whether to issue a missing res notification
					# we need the localized resource name here
					elif building in self.buildings_missing_resources:
						res_name = self.session.db.get_res_name(self.buildings_missing_resources[building])
						self.session.ingame_gui.message_widget.add(
						  point=building.position.origin,
						  string_id='NEED_MORE_RES', message_dict={'resource': res_name})

		self.buildings = []
		self.buildings_action_set_ids = []
		return changed_tiles

	def _check_update_preview(self, end_point):
		"""Used internally if the end_point changes"""
		if self.end_point != end_point:
			self.end_point = end_point
			self.update_preview()

	def _remove_listeners(self):
		"""Resets the ChangeListener for update_preview."""
		if self.last_change_listener is not None:
			self.last_change_listener.discard_change_listener(self.force_update)
			self.last_change_listener.discard_change_listener(self.highlight_buildable)
			self._build_logic.remove_change_listener(self.last_change_listener, self)

		self.last_change_listener = None

	def _add_listeners(self, instance):
		if self.last_change_listener != instance:
			self._remove_listeners()
			self.last_change_listener = instance
			if self.last_change_listener is not None:
				self._build_logic.add_change_listener(self.last_change_listener, self)

	def force_update(self):
		self.update_preview(force=True)

	def update_preview(self, force=False):
		"""Used as callback method"""
		if self.start_point is not None:
			end_point = self.end_point or self.start_point
			self.preview_build(self.start_point, end_point, force=force)

	def _rotate(self, degrees):
		self.rotation = (self.rotation + degrees) % 360
		self.log.debug("BuildingTool: Building rotation now: %s", self.rotation)
		self.update_preview()
		self.draw_gui()

	def rotate_left(self):
		self._rotate(degrees=90)

	def rotate_right(self):
		self._rotate(degrees=270)

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
		for fife_instance in self.buildings_fife_instances.values():
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
					fife_instance.get2dGfxVisual().setTransparency(BUILDINGS.TRANSPARENCY_VALUE)
		self._transparencified_instances.clear()

	def _remove_coloring(self):
		"""Removes coloring from tiles, that indicate that the tile is buildable
		as well as all highlights. Called when building mode is finished."""
		for building in self._related_buildings:
			building.get_component(SelectableComponent).deselect()
		self.renderer.removeAllOutlines()
		self.renderer.removeAllColored()


class ShipBuildingToolLogic:
	"""Helper class to separate the logic needed when building from a ship from
	the main building tool."""

	def __init__(self, ship):
		self.ship = ship

	def highlight_buildable(self, building_tool, tiles_to_check=None):
		"""Highlights all buildable tiles.
		@param tiles_to_check: list of tiles to check for coloring."""
		# resolved variables from inner loops
		is_tile_buildable = building_tool._class.is_tile_buildable
		session = building_tool.session
		player = session.world.player
		buildable_tiles_add = building_tool._buildable_tiles.add

		if tiles_to_check is not None: # only check these tiles (build from ship)
			for tile in tiles_to_check:
				if is_tile_buildable(session, tile, self.ship):
					building_tool._color_buildable_tile(tile)
		else: # build from ship
			building_tool.renderer.removeAllColored()
			for island in session.world.get_islands_in_radius(self.ship.position, self.ship.radius):
				for tile in island.get_surrounding_tiles(self.ship.position, self.ship.radius):
					if is_tile_buildable(session, tile, self.ship):
						buildable_tiles_add(tile)
						# check that there is no other player's settlement
						if tile.settlement is None or tile.settlement.owner == player:
							building_tool._color_buildable_tile(tile)

	def on_escape(self, session):
		for selected in session.selected_instances:
			selected.get_component(SelectableComponent).deselect()
		session.selected_instances = set([self.ship])
		self.ship.get_component(SelectableComponent).select()
		self.ship.get_component(SelectableComponent).show_menu()

	def remove(self, session):
		self.on_escape(session)

	def add_change_listener(self, instance, building_tool):
		# instance is self.ship here
		instance.add_change_listener(building_tool.highlight_buildable)
		instance.add_change_listener(building_tool.force_update)

	def remove_change_listener(self, instance, building_tool):
		# be idempotent
		instance.discard_change_listener(building_tool.highlight_buildable)
		instance.discard_change_listener(building_tool.force_update)

	# Using messages now.
	def continue_build(self):
		pass


class SettlementBuildingToolLogic:
	"""Helper class to separate the logic needed when building from a settlement
	from the main building tool"""

	def __init__(self, building_tool):
		self.building_tool = weakref.ref(building_tool)
		self.subscribed = False

	def highlight_buildable(self, building_tool, tiles_to_check=None):
		"""Highlights all buildable tiles.
		@param tiles_to_check: list of tiles to check for coloring."""

		# resolved variables from inner loops
		is_tile_buildable = building_tool._class.is_tile_buildable
		session = building_tool.session
		player = session.world.player

		if not self.subscribed:
			self.subscribed = True
			SettlementRangeChanged.subscribe(self._on_update)

		if tiles_to_check is not None:
			# Only check these tiles.
			for tile in tiles_to_check:
				if is_tile_buildable(session, tile, None):
					building_tool._color_buildable_tile(tile)
		else:
			# Default build on island.
			for settlement in session.world.settlements:
				if settlement.owner == player:
					island = session.world.get_island(Point(*next(iter(settlement.ground_map.keys()))))
					for tile in settlement.ground_map.values():
						if is_tile_buildable(session, tile, None, island, check_settlement=False):
							building_tool._color_buildable_tile(tile)

	def _on_update(self, message):
		if self.building_tool() and message.sender.owner.is_local_player:
			# this is generally caused by adding new buildings, therefore new_buildings=True
			self.building_tool().highlight_buildable(message.changed_tiles, new_buildings=True)

	def on_escape(self, session):
		session.ingame_gui.show_build_menu()  # This will call remove().
		if self.subscribed:
			self.subscribed = False
			SettlementRangeChanged.unsubscribe(self._on_update)

	def remove(self, session):
		if self.subscribed:
			self.subscribed = False
			SettlementRangeChanged.unsubscribe(self._on_update)

	# Using messages now.
	def add_change_listener(self, instance, building_tool):
		pass

	def remove_change_listener(self, instance, building_tool):
		pass

	def continue_build(self):
		pass


class BuildRelatedBuildingToolLogic(SettlementBuildingToolLogic):
	"""Same as normal build, except quitting it drops to the build related tab."""
	def __init__(self, building_tool, instance):
		super().__init__(building_tool)
		# instance must be weakref
		self.instance = instance

	def _reshow_tab(self):
		from horizons.gui.tabs import BuildRelatedTab
		self.instance().get_component(SelectableComponent).show_menu(jump_to_tabclass=BuildRelatedTab)

	def on_escape(self, session):
		super().on_escape(session)
		self._reshow_tab()

	def continue_build(self):
		self._reshow_tab()
