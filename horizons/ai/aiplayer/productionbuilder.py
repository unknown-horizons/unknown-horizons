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

import itertools
from collections import deque
from functools import partial

from horizons.ai.aiplayer.basicbuilder import BasicBuilder
from horizons.command.building import Tear
from horizons.command.production import ToggleActive
from horizons.component.namedcomponent import NamedComponent
from horizons.constants import AI, BUILDINGS
from horizons.entities import Entities
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback
from horizons.util.shapes import Rect, distances
from horizons.world.buildability.binarycache import BinaryBuildabilityCache
from horizons.world.buildability.potentialroadconnectivitycache import (
	PotentialRoadConnectivityCache)
from horizons.world.buildability.simplecollectorareacache import SimpleCollectorAreaCache
from horizons.world.building.production import Mine
from horizons.world.production.producer import Producer

from .areabuilder import AreaBuilder
from .constants import BUILD_RESULT, BUILDING_PURPOSE


class ProductionBuilder(AreaBuilder):
	"""
	An object of this class manages the production area of a settlement.

	Important attributes:
	* plan: a dictionary of the form {(x, y): (purpose, extra data), ...} where purpose is one of the BUILDING_PURPOSE constants.
		Coordinates being in the plan means that the tile doesn't belong to another player.
	* collector_buildings: a list of every building in the settlement that provides general collectors (warehouse, storages)
	* production_buildings: a list of buildings in the settlement where productions should be paused and resumed at appropriate times
	* unused_fields: a dictionary where the key is a BUILDING_PURPOSE constant of a field and the value is a deque that holds the
		coordinates of unused field spots. {building purpose: deque([(x, y), ...]), ...}
	* last_collector_improvement_storage: the last tick when a storage was built to improve collector coverage
	* last_collector_improvement_road: the last tick when a new road connection was built to improve collector coverage
	"""

	coastal_building_classes = [BUILDINGS.FISHER, BUILDINGS.BOAT_BUILDER, BUILDINGS.SALT_PONDS]

	def __init__(self, settlement_manager):
		super().__init__(settlement_manager)
		self.plan = dict.fromkeys(self.land_manager.production, (BUILDING_PURPOSE.NONE, None))
		self.__init(settlement_manager, Scheduler().cur_tick, Scheduler().cur_tick)
		self._init_buildability_cache()
		self._init_simple_collector_area_cache()
		self._init_road_connectivity_cache()
		self.register_change_list(list(settlement_manager.settlement.warehouse.position.tuple_iter()),
		                          BUILDING_PURPOSE.WAREHOUSE, None)
		self._refresh_unused_fields()

	def __init(self, settlement_manager, last_collector_improvement_storage, last_collector_improvement_road):
		self._init_cache()
		self.collector_buildings = [] # [building, ...]
		self.production_buildings = [] # [building, ...]
		self.personality = self.owner.personality_manager.get('ProductionBuilder')
		self.last_collector_improvement_storage = last_collector_improvement_storage
		self.last_collector_improvement_road = last_collector_improvement_road

	def _init_buildability_cache(self):
		self.buildability_cache = BinaryBuildabilityCache(self.island.terrain_cache)
		free_coords_set = set()
		for coords, (purpose, _) in self.plan.items():
			if purpose == BUILDING_PURPOSE.NONE:
				free_coords_set.add(coords)
		for coords in self.land_manager.coastline:
			free_coords_set.add(coords)
		self.buildability_cache.add_area(free_coords_set)

	def _init_simple_collector_area_cache(self):
		self.simple_collector_area_cache = SimpleCollectorAreaCache(self.island.terrain_cache)

	def _init_road_connectivity_cache(self):
		self.road_connectivity_cache = PotentialRoadConnectivityCache(self)
		coords_set = set()
		for coords in self.plan:
			coords_set.add(coords)
		for coords in self.land_manager.roads:
			coords_set.add(coords)
		self.road_connectivity_cache.modify_area(list(sorted(coords_set)))

	def save(self, db):
		super().save(db)
		translated_last_collector_improvement_storage = self.last_collector_improvement_storage - Scheduler().cur_tick # pre-translate for the loading process
		translated_last_collector_improvement_road = self.last_collector_improvement_road - Scheduler().cur_tick # pre-translate for the loading process
		db("INSERT INTO ai_production_builder(rowid, settlement_manager, last_collector_improvement_storage, last_collector_improvement_road) VALUES(?, ?, ?, ?)",
			self.worldid, self.settlement_manager.worldid, translated_last_collector_improvement_storage, translated_last_collector_improvement_road)
		for (x, y), (purpose, _) in self.plan.items():
			db("INSERT INTO ai_production_builder_plan(production_builder, x, y, purpose) VALUES(?, ?, ?, ?)", self.worldid, x, y, purpose)

	def _load(self, db, settlement_manager):
		worldid, last_storage, last_road = \
			db("SELECT rowid, last_collector_improvement_storage, last_collector_improvement_road FROM ai_production_builder WHERE settlement_manager = ?",
			settlement_manager.worldid)[0]
		super()._load(db, settlement_manager, worldid)
		self.__init(settlement_manager, last_storage, last_road)

		db_result = db("SELECT x, y, purpose FROM ai_production_builder_plan WHERE production_builder = ?", worldid)
		for x, y, purpose in db_result:
			self.plan[(x, y)] = (purpose, None)
			if purpose == BUILDING_PURPOSE.ROAD:
				self.land_manager.roads.add((x, y))
		self._init_buildability_cache()
		self._init_simple_collector_area_cache()
		self._init_road_connectivity_cache()
		self._refresh_unused_fields()

	def have_deposit(self, resource_id):
		"""Returns True if there is a resource deposit of the relevant type inside the settlement."""
		for tile in self.land_manager.resource_deposits[resource_id]:
			if tile.object.settlement is None:
				continue
			coords = tile.object.position.origin.to_tuple()
			if coords in self.settlement.ground_map:
				return True
		return False

	def extend_settlement_with_storage(self, target_position):
		"""Build a storage to extend the settlement towards the given position. Return a BUILD_RESULT constant."""
		if not self.have_resources(BUILDINGS.STORAGE):
			return BUILD_RESULT.NEED_RESOURCES

		storage_class = Entities.buildings[BUILDINGS.STORAGE]
		storage_spots = self.island.terrain_cache.get_buildability_intersection(storage_class.terrain_type,
			storage_class.size, self.settlement.buildability_cache, self.buildability_cache)
		storage_surrounding_offsets = Rect.get_surrounding_offsets(storage_class.size)
		coastline = self.land_manager.coastline

		options = []
		for (x, y) in sorted(storage_spots):
			builder = BasicBuilder.create(BUILDINGS.STORAGE, (x, y), 0)

			alignment = 1
			for (dx, dy) in storage_surrounding_offsets:
				coords = (x + dx, y + dy)
				if coords in coastline or coords not in self.plan or self.plan[coords][0] != BUILDING_PURPOSE.NONE:
					alignment += 1

			distance = distances.distance_rect_rect(target_position, builder.position)
			value = distance - alignment * 0.7
			options.append((-value, builder))
		return self.build_best_option(options, BUILDING_PURPOSE.STORAGE)

	def get_collector_area(self):
		"""Return the set of all coordinates that are reachable from at least one collector by road or open space."""
		if self.__collector_area_cache is not None and self.last_change_id == self.__collector_area_cache[0]:
			return self.__collector_area_cache[1]

		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		collector_area = set() # unused tiles that are reachable from at least one collector
		for building in self.collector_buildings:
			coverage_area = set()
			for coords in building.position.get_radius_coordinates(building.radius, True):
				coverage_area.add(coords)

			reachable = set()
			queue = deque()
			for coords in building.position.tuple_iter():
				reachable.add(coords)
				queue.append(coords)

			while queue:
				x, y = queue.popleft()
				for dx, dy in moves:
					coords = (x + dx, y + dy)
					if coords not in reachable and coords in coverage_area:
						if coords in self.land_manager.roads or (coords in self.plan and coords not in self.land_manager.coastline and self.plan[coords][0] == BUILDING_PURPOSE.NONE):
							queue.append(coords)
							reachable.add(coords)
							if coords in self.plan and self.plan[coords][0] == BUILDING_PURPOSE.NONE:
								collector_area.add(coords)
		self.__collector_area_cache = (self.last_change_id, collector_area)
		return collector_area

	def count_available_squares(self, size, max_num=None):
		"""
		Count the number of available and usable (covered by collectors) size x size squares.

		@param size: the square side length
		@param max_num: if non-None then stop counting once the number of total squares is max_num
		@return: (available squares, total squares)
		"""

		key = (size, max_num)
		if key in self.__available_squares_cache and self.last_change_id == self.__available_squares_cache[key][0]:
			return self.__available_squares_cache[key][1]

		offsets = list(itertools.product(range(size), range(size)))
		collector_area = self.get_collector_area()

		available_squares = 0
		total_squares = 0
		for x, y in self.plan:
			ok = True
			accessible = False
			for dx, dy in offsets:
				coords = (x + dx, y + dy)
				if coords not in self.plan or self.plan[coords][0] != BUILDING_PURPOSE.NONE:
					ok = False
					break
				if coords in collector_area:
					accessible = True
			if ok:
				total_squares += 1
				if max_num is not None and total_squares >= max_num:
					break
				if accessible:
					available_squares += 1
		self.__available_squares_cache[key] = (self.last_change_id, (available_squares, total_squares))
		return self.__available_squares_cache[key][1]

	def _refresh_unused_fields(self):
		"""Refresh the unused_fields object to make sure no impossible fields spots are in the list."""
		self.unused_fields = {
			BUILDING_PURPOSE.POTATO_FIELD: deque(),
			BUILDING_PURPOSE.PASTURE: deque(),
			BUILDING_PURPOSE.SUGARCANE_FIELD: deque(),
			BUILDING_PURPOSE.TOBACCO_FIELD: deque(),
			BUILDING_PURPOSE.HERBARY: deque(),
		}

		for coords, (purpose, _) in sorted(self.plan.items()):
			usable = True # is every tile of the field spot still usable for new normal buildings
			for dx in range(3):
				for dy in range(3):
					coords2 = (coords[0] + dx, coords[1] + dy)
					if coords2 not in self.island.ground_map:
						usable = False
					else:
						object = self.island.ground_map[coords2].object
						if object is not None and not object.buildable_upon:
							usable = False
							break
			if usable and purpose in self.unused_fields:
				self.unused_fields[purpose].append(coords)

	def display(self):
		"""Show the plan on the map unless it is disabled in the settings."""
		if not AI.HIGHLIGHT_PLANS:
			return

		tile_colors = {
			BUILDING_PURPOSE.ROAD: (30, 30, 30),
			BUILDING_PURPOSE.FISHER: (128, 128, 128),
			BUILDING_PURPOSE.LUMBERJACK: (30, 255, 30),
			BUILDING_PURPOSE.TREE: (0, 255, 0),
			BUILDING_PURPOSE.FARM: (128, 0, 255),
			BUILDING_PURPOSE.POTATO_FIELD: (255, 0, 128),
			BUILDING_PURPOSE.PASTURE: (0, 192, 0),
			BUILDING_PURPOSE.WEAVER: (0, 64, 64),
			BUILDING_PURPOSE.SUGARCANE_FIELD: (192, 192, 0),
			BUILDING_PURPOSE.DISTILLERY: (255, 128, 40),
			BUILDING_PURPOSE.TOBACCO_FIELD: (64, 64, 0),
			BUILDING_PURPOSE.TOBACCONIST: (128, 64, 40),
			BUILDING_PURPOSE.CLAY_PIT: (0, 64, 0),
			BUILDING_PURPOSE.BRICKYARD: (0, 32, 0),
			BUILDING_PURPOSE.BOAT_BUILDER: (163, 73, 164),
			BUILDING_PURPOSE.SALT_PONDS: (153, 217, 234),
			BUILDING_PURPOSE.HERBARY: (64, 200, 0),
			BUILDING_PURPOSE.RESERVED: (0, 0, 128),
		}

		misc_color = (0, 255, 255)
		unknown_color = (128, 0, 0)
		renderer = self.session.view.renderer['InstanceRenderer']

		for coords, (purpose, _) in self.plan.items():
			tile = self.island.ground_map[coords]
			color = tile_colors.get(purpose, misc_color)
			if purpose == BUILDING_PURPOSE.NONE:
				color = unknown_color
			renderer.addColored(tile._instance, *color)

	def _init_cache(self):
		"""Initialize the cache that knows the last time the buildability of a rectangle may have changed in this area."""
		super()._init_cache()
		self.__collector_area_cache = None
		self.__available_squares_cache = {}

	def register_change(self, x, y, purpose, data):
		"""Register the possible buildability change of a rectangle on this island."""
		super().register_change(x, y, purpose, data)
		coords = (x, y)
		if coords in self.land_manager.village or (coords not in self.plan and coords not in self.land_manager.coastline):
			return
		self.last_change_id += 1

	def register_change_list(self, coords_list, purpose, data):
		add_list = []
		remove_list = []
		for coords in coords_list:
			if coords in self.land_manager.village or coords not in self.plan:
				continue
			if purpose == BUILDING_PURPOSE.NONE and self.plan[coords][0] != BUILDING_PURPOSE.NONE:
				add_list.append(coords)
			elif purpose != BUILDING_PURPOSE.NONE and self.plan[coords][0] == BUILDING_PURPOSE.NONE:
				remove_list.append(coords)
		if add_list:
			self.buildability_cache.add_area(add_list)
		if remove_list:
			self.buildability_cache.remove_area(remove_list)

		super().register_change_list(coords_list, purpose, data)
		self.road_connectivity_cache.modify_area(coords_list)
		self.display()

	def handle_lost_area(self, coords_list):
		"""Handle losing the potential land in the given coordinates list."""
		# remove planned fields that are now impossible
		lost_coords_list = []
		for coords in coords_list:
			if coords in self.plan:
				lost_coords_list.append(coords)
		self.register_change_list(lost_coords_list, BUILDING_PURPOSE.NONE, None)

		field_size = Entities.buildings[BUILDINGS.POTATO_FIELD].size
		removed_list = []
		for coords, (purpose, _) in self.plan.items():
			if purpose in [BUILDING_PURPOSE.POTATO_FIELD, BUILDING_PURPOSE.PASTURE, BUILDING_PURPOSE.SUGARCANE_FIELD, BUILDING_PURPOSE.TOBACCO_FIELD, BUILDING_PURPOSE.HERBARY]:
				rect = Rect.init_from_topleft_and_size_tuples(coords, field_size)
				for field_coords in rect.tuple_iter():
					if field_coords not in self.land_manager.production:
						removed_list.append(coords)
						break

		for coords in removed_list:
			rect = Rect.init_from_topleft_and_size_tuples(coords, field_size)
			self.register_change_list(list(rect.tuple_iter()), BUILDING_PURPOSE.NONE, None)
		self._refresh_unused_fields()
		super().handle_lost_area(coords_list)
		self.road_connectivity_cache.modify_area(lost_coords_list)

	def handle_new_area(self):
		"""Handle receiving more land to the production area (this can happen when the village area gives some up)."""
		new_coords_list = []
		for coords in self.land_manager.production:
			if coords not in self.plan:
				new_coords_list.append(coords)
		self.register_change_list(new_coords_list, BUILDING_PURPOSE.NONE, None)

	collector_building_classes = [BUILDINGS.WAREHOUSE, BUILDINGS.STORAGE]
	field_building_classes = [BUILDINGS.POTATO_FIELD, BUILDINGS.PASTURE, BUILDINGS.SUGARCANE_FIELD, BUILDINGS.TOBACCO_FIELD]
	production_building_classes = {BUILDINGS.FISHER, BUILDINGS.LUMBERJACK, BUILDINGS.FARM, BUILDINGS.CLAY_PIT,
		BUILDINGS.BRICKYARD, BUILDINGS.WEAVER, BUILDINGS.DISTILLERY, BUILDINGS.MINE, BUILDINGS.SMELTERY,
		BUILDINGS.TOOLMAKER, BUILDINGS.CHARCOAL_BURNER, BUILDINGS.TOBACCONIST, BUILDINGS.SALT_PONDS}

	def add_building(self, building):
		"""Called when a new building is added in the area (the building already exists during the call)."""
		if building.id in self.collector_building_classes:
			self.collector_buildings.append(building)
			self.simple_collector_area_cache.add_building(building)
		elif building.id in self.production_building_classes:
			self.production_buildings.append(building)

		super().add_building(building)

	def _handle_lumberjack_removal(self, building):
		"""Release the unused trees around the lumberjack building being removed."""
		trees_used_by_others = set()
		for lumberjack_building in self.settlement.buildings_by_id.get(BUILDINGS.LUMBERJACK, []):
			if lumberjack_building.worldid == building.worldid:
				continue
			for coords in lumberjack_building.position.get_radius_coordinates(lumberjack_building.radius):
				if coords in self.plan and self.plan[coords][0] == BUILDING_PURPOSE.TREE:
					trees_used_by_others.add(coords)

		coords_list = []
		for coords in building.position.get_radius_coordinates(building.radius):
			if coords not in trees_used_by_others and coords in self.plan and self.plan[coords][0] == BUILDING_PURPOSE.TREE:
				coords_list.append(coords)
		self.register_change_list(coords_list, BUILDING_PURPOSE.NONE, None)

	def _handle_farm_removal(self, building):
		"""Handle farm removal by removing planned fields and tearing existing ones that can't be serviced by another farm."""
		unused_fields = set()
		farms = self.settlement.buildings_by_id.get(BUILDINGS.FARM, [])
		for coords in building.position.get_radius_coordinates(building.radius):
			if coords not in self.plan:
				continue
			object = self.island.ground_map[coords].object
			if object is None or object.id not in self.field_building_classes:
				continue

			used_by_another_farm = False
			for farm in farms:
				if farm.worldid != building.worldid and object.position.distance(farm.position) <= farm.radius:
					used_by_another_farm = True
					break
			if not used_by_another_farm:
				unused_fields.add(object)

		# tear the finished but no longer used fields down
		for unused_field in unused_fields:
			self.register_change_list(list(unused_field.position.tuple_iter()), BUILDING_PURPOSE.NONE, None)
			Tear(unused_field).execute(self.session)

		# remove the planned but never built fields from the plan
		self._refresh_unused_fields()
		for unused_fields_list in self.unused_fields.values():
			for coords in unused_fields_list:
				position = Rect.init_from_topleft_and_size_tuples(coords, Entities.buildings[BUILDINGS.POTATO_FIELD].size)
				if building.position.distance(position) > building.radius:
					continue # it never belonged to the removed building

				used_by_another_farm = False
				for farm in farms:
					if farm.worldid != building.worldid and position.distance(farm.position) <= farm.radius:
						used_by_another_farm = True
						break
				if not used_by_another_farm:
					self.register_change_list(list(position.tuple_iter()), BUILDING_PURPOSE.NONE, None)
		self._refresh_unused_fields()

	def remove_building(self, building):
		"""Called when a building is removed from the area (the building still exists during the call)."""
		if building.id in self.field_building_classes:
			# this can't be handled right now because the building still exists
			Scheduler().add_new_object(Callback(self._refresh_unused_fields), self, run_in=0)
			Scheduler().add_new_object(Callback(partial(super().remove_building, building)), self, run_in=0)
		elif building.buildable_upon or building.id == BUILDINGS.TRAIL:
			pass # don't react to road, trees and ruined tents being destroyed
		else:
			self.register_change_list(list(building.position.tuple_iter()), BUILDING_PURPOSE.NONE, None)

			if building.id in self.collector_building_classes:
				self.collector_buildings.remove(building)
				self.simple_collector_area_cache.remove_building(building)
			elif building.id in self.production_building_classes:
				self.production_buildings.remove(building)

			if building.id == BUILDINGS.LUMBERJACK:
				self._handle_lumberjack_removal(building)
			elif building.id == BUILDINGS.FARM:
				self._handle_farm_removal(building)

			super().remove_building(building)

	def manage_production(self):
		"""Pauses and resumes production buildings when they have full input and output inventories."""
		for building in self.production_buildings:
			producer = building.get_component(Producer)
			for production in producer.get_productions():
				if not production.get_produced_resources():
					continue
				all_full = True

				# inventory full of the produced resources?
				for resource_id, min_amount in production.get_produced_resources().items():
					if production.inventory.get_free_space_for(resource_id) >= min_amount:
						all_full = False
						break

				# inventory full of the input resource?
				if all_full and not isinstance(building, Mine):
					for resource_id in production.get_consumed_resources():
						if production.inventory.get_free_space_for(resource_id) > 0:
							all_full = False
							break

				if all_full:
					if not production.is_paused():
						ToggleActive(producer, production).execute(self.land_manager.session)
						self.log.info('%s paused a production at %s/%d', self, building.name, building.worldid)
				else:
					if production.is_paused():
						ToggleActive(producer, production).execute(self.land_manager.session)
						self.log.info('%s resumed a production at %s/%d', self, building.name, building.worldid)

	def handle_mine_empty(self, mine):
		Tear(mine).execute(self.session)
		self.land_manager.refresh_resource_deposits()

	def __str__(self):
		return '{}.PB({}/{})'.format(
			self.owner,
			self.settlement.get_component(NamedComponent).name if hasattr(
				self, 'settlement') else 'unknown',
			self.worldid if hasattr(self, 'worldid') else 'none')
