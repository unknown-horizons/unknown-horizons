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

import itertools

from collections import deque
from functools import partial

from builder import Builder
from areabuilder import AreaBuilder
from constants import BUILD_RESULT, BUILDING_PURPOSE

from horizons.world.building.production import Mine
from horizons.command.building import Tear
from horizons.command.production import ToggleActive
from horizons.constants import AI, BUILDINGS
from horizons.scheduler import Scheduler
from horizons.util import Callback, Point, Rect
from horizons.util.python import decorators
from horizons.entities import Entities
from horizons.world.production.producer import Producer
from horizons.world.component.namedcomponent import NamedComponent

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

	coastal_building_classes = [BUILDINGS.FISHERMAN_CLASS, BUILDINGS.BOATBUILDER_CLASS, BUILDINGS.SALT_PONDS_CLASS]

	def __init__(self, settlement_manager):
		super(ProductionBuilder, self).__init__(settlement_manager)
		self.plan = dict.fromkeys(self.land_manager.production, (BUILDING_PURPOSE.NONE, None))
		self.__init(settlement_manager, Scheduler().cur_tick, Scheduler().cur_tick)
		for x, y in settlement_manager.settlement.warehouse.position.tuple_iter():
			self.register_change(x, y, BUILDING_PURPOSE.WAREHOUSE, None)
		self._refresh_unused_fields()

	def __init(self, settlement_manager, last_collector_improvement_storage, last_collector_improvement_road):
		self._init_cache()
		self.collector_buildings = [] # [building, ...]
		self.production_buildings = [] # [building, ...]
		self.personality = self.owner.personality_manager.get('ProductionBuilder')
		self.last_collector_improvement_storage = last_collector_improvement_storage
		self.last_collector_improvement_road = last_collector_improvement_road
		self.__builder_cache = {}

	def save(self, db):
		super(ProductionBuilder, self).save(db)
		translated_last_collector_improvement_storage = self.last_collector_improvement_storage - Scheduler().cur_tick # pre-translate for the loading process
		translated_last_collector_improvement_road = self.last_collector_improvement_road - Scheduler().cur_tick # pre-translate for the loading process
		db("INSERT INTO ai_production_builder(rowid, settlement_manager, last_collector_improvement_storage, last_collector_improvement_road) VALUES(?, ?, ?, ?)", \
			self.worldid, self.settlement_manager.worldid, translated_last_collector_improvement_storage, translated_last_collector_improvement_road)
		for (x, y), (purpose, _) in self.plan.iteritems():
			db("INSERT INTO ai_production_builder_plan(production_builder, x, y, purpose) VALUES(?, ?, ?, ?)", self.worldid, x, y, purpose)

	def _load(self, db, settlement_manager):
		worldid, last_storage, last_road = \
			db("SELECT rowid, last_collector_improvement_storage, last_collector_improvement_road FROM ai_production_builder WHERE settlement_manager = ?", \
			settlement_manager.worldid)[0]
		super(ProductionBuilder, self)._load(db, settlement_manager, worldid)
		self.__init(settlement_manager, last_storage, last_road)

		db_result = db("SELECT x, y, purpose FROM ai_production_builder_plan WHERE production_builder = ?", worldid)
		for x, y, purpose in db_result:
			self.plan[(x, y)] = (purpose, None)
			if purpose == BUILDING_PURPOSE.ROAD:
				self.land_manager.roads.add((x, y))
		self._refresh_unused_fields()

	def have_deposit(self, resource_id):
		"""Returns true if there is a resource deposit of the relevant type inside the settlement."""
		for tile in self.land_manager.resource_deposits[resource_id]:
			if tile.object.settlement is None:
				continue
			coords = tile.object.position.origin.to_tuple()
			if coords in self.settlement.ground_map:
				return True
		return False

	def build_best_option(self, options, purpose):
		"""
		Try to build the highest valued option. Return a BUILD_RESULT constant showing how it went.

		@param options: [(value, builder), ...]
		@param purpose: a BUILDING_PURPOSE constant
		"""

		if not options:
			return BUILD_RESULT.IMPOSSIBLE

		builder = max(options)[1]
		if not builder.execute():
			return BUILD_RESULT.UNKNOWN_ERROR
		for x, y in builder.position.tuple_iter():
			self.register_change(x, y, BUILDING_PURPOSE.RESERVED, None)
		self.register_change(builder.position.origin.x, builder.position.origin.y, purpose, None)
		return BUILD_RESULT.OK

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
				x, y = queue[0]
				queue.popleft()
				for dx, dy in moves:
					coords = (x + dx, y + dy)
					if coords not in reachable and coords in coverage_area:
						if coords in self.land_manager.roads or (coords in self.plan and self.plan[coords][0] == BUILDING_PURPOSE.NONE):
							queue.append(coords)
							reachable.add(coords)
							if coords in self.plan and self.plan[coords][0] == BUILDING_PURPOSE.NONE:
								collector_area.add(coords)
		self.__collector_area_cache = (self.last_change_id, collector_area)
		return collector_area

	def count_available_squares(self, size, max_num = None):
		"""
		Count the number of available and usable (covered by collectors) size x size squares.

		@param size: the square side length
		@param max_num: if non-None then stop counting once the number of total squares is max_num
		@return: (available squares, total squares)
		"""

		key = (size, max_num)
		if key in self.__available_squares_cache and self.last_change_id == self.__available_squares_cache[key][0]:
			return self.__available_squares_cache[key][1]

		offsets = list(itertools.product(xrange(size), xrange(size)))
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
		}

		for coords, (purpose, _) in sorted(self.plan.iteritems()):
			usable = True # is every tile of the field spot still usable for new normal buildings
			for dx in xrange(3):
				for dy in xrange(3):
					coords2 = (coords[0] + dx, coords[1] + dy)
					object = self.island.ground_map[coords2].object
					if object is not None and not object.buildable_upon:
						usable = False
			if usable and purpose in self.unused_fields:
				self.unused_fields[purpose].append(coords)

	def display(self):
		"""Show the plan on the map unless it is disabled in the settings."""
		if not AI.HIGHLIGHT_PLANS:
			return

		road_colour = (30, 30, 30)
		fisher_colour = (128, 128, 128)
		lumberjack_colour = (30, 255, 30)
		tree_colour = (0, 255, 0)
		reserved_colour = (0, 0, 128)
		unknown_colour = (128, 0, 0)
		farm_colour = (128, 0, 255)
		potato_field_colour = (255, 0, 128)
		pasture_colour = (0, 192, 0)
		weaver_colour = (0, 64, 64)
		sugarcane_field_colour = (192, 192, 0)
		distillery_colour = (255, 128, 40)
		tobacco_field_colour = (64, 64, 0)
		tobacconist_colour = (128, 64, 40)
		clay_pit_colour = (0, 64, 0)
		brickyard_colour = (0, 32, 0)
		boatbuilder_colour = (163, 73, 164)
		salt_ponds_colour = (153, 217, 234)
		misc_colour = (0, 255, 255)
		renderer = self.session.view.renderer['InstanceRenderer']

		for coords, (purpose, _) in self.plan.iteritems():
			tile = self.island.ground_map[coords]
			if purpose == BUILDING_PURPOSE.ROAD:
				renderer.addColored(tile._instance, *road_colour)
			elif purpose == BUILDING_PURPOSE.FISHER:
				renderer.addColored(tile._instance, *fisher_colour)
			elif purpose == BUILDING_PURPOSE.LUMBERJACK:
				renderer.addColored(tile._instance, *lumberjack_colour)
			elif purpose == BUILDING_PURPOSE.TREE:
				renderer.addColored(tile._instance, *tree_colour)
			elif purpose == BUILDING_PURPOSE.FARM:
				renderer.addColored(tile._instance, *farm_colour)
			elif purpose == BUILDING_PURPOSE.POTATO_FIELD:
				renderer.addColored(tile._instance, *potato_field_colour)
			elif purpose == BUILDING_PURPOSE.PASTURE:
				renderer.addColored(tile._instance, *pasture_colour)
			elif purpose == BUILDING_PURPOSE.WEAVER:
				renderer.addColored(tile._instance, *weaver_colour)
			elif purpose == BUILDING_PURPOSE.SUGARCANE_FIELD:
				renderer.addColored(tile._instance, *sugarcane_field_colour)
			elif purpose == BUILDING_PURPOSE.DISTILLERY:
				renderer.addColored(tile._instance, *distillery_colour)
			elif purpose == BUILDING_PURPOSE.TOBACCO_FIELD:
				renderer.addColored(tile._instance, *tobacco_field_colour)
			elif purpose == BUILDING_PURPOSE.TOBACCONIST:
				renderer.addColored(tile._instance, *tobacconist_colour)
			elif purpose == BUILDING_PURPOSE.CLAY_PIT:
				renderer.addColored(tile._instance, *clay_pit_colour)
			elif purpose == BUILDING_PURPOSE.BRICKYARD:
				renderer.addColored(tile._instance, *brickyard_colour)
			elif purpose == BUILDING_PURPOSE.BOAT_BUILDER:
				renderer.addColored(tile._instance, *boatbuilder_colour)
			elif purpose == BUILDING_PURPOSE.SALT_PONDS:
				renderer.addColored(tile._instance, *salt_ponds_colour)
			elif purpose == BUILDING_PURPOSE.RESERVED:
				renderer.addColored(tile._instance, *reserved_colour)
			elif purpose != BUILDING_PURPOSE.NONE:
				renderer.addColored(tile._instance, *misc_colour)
			else:
				renderer.addColored(tile._instance, *unknown_colour)

	def __make_new_builder(self, building_id, x, y, needs_collector, orientation):
		"""Return a Builder object if it is allowed to be built at the location, otherwise return None (not cached)."""
		coords = (x, y)
		# quick check to see whether the origin square is allowed to be in the requested place
		if building_id == BUILDINGS.CLAY_PIT_CLASS or building_id == BUILDINGS.IRON_MINE_CLASS:
			# clay deposits and mountains are outside the production plan until they are constructed
			if coords in self.plan or coords not in self.settlement.ground_map:
				return None
		elif building_id in self.coastal_building_classes:
			# coastal buildings can use coastal tiles
			if coords not in self.land_manager.coastline and coords in self.plan and self.plan[coords][0] != BUILDING_PURPOSE.NONE:
				return None
		else:
			if coords not in self.plan or self.plan[coords][0] != BUILDING_PURPOSE.NONE or coords not in self.settlement.ground_map:
				return None

		# create the builder, make sure that it is allowed according to the game logic
		builder = Builder.create(building_id, self.land_manager, Point(x, y), orientation=orientation)
		if not builder or not self.land_manager.legal_for_production(builder.position):
			return None

		# make sure that the position of the building is allowed according to the plan
		if building_id in self.coastal_building_classes:
			# coastal buildings can use coastal tiles
			for coords in builder.position.tuple_iter():
				if coords not in self.land_manager.coastline and coords in self.plan and self.plan[coords][0] != BUILDING_PURPOSE.NONE:
					return None
		elif building_id in [BUILDINGS.CLAY_PIT_CLASS, BUILDINGS.IRON_MINE_CLASS]:
			# clay deposits and mountains can't be in areas restricted by the plan
			pass
		else:
			for coords in builder.position.tuple_iter():
				if coords not in self.plan or self.plan[coords][0] != BUILDING_PURPOSE.NONE:
					return None

		# make sure the building is close enough to a collector if it produces any resources that have to be collected
		if needs_collector and not any(True for building in self.collector_buildings if building.position.distance(builder.position) <= building.radius):
			return None
		return builder

	def make_builder(self, building_id, x, y, needs_collector, orientation = 0):
		"""Return a Builder object if it is allowed to be built at the location, otherwise return None (cached)."""
		coords = (x, y)
		key = (building_id, coords, needs_collector, orientation)
		size = Entities.buildings[building_id].size
		if orientation == 1 or orientation == 3:
			size = (size[1], size[0])
		if coords not in self.island.last_changed[size]:
			return None

		island_changed = self.island.last_changed[size][coords]
		if key in self.__builder_cache and island_changed != self.__builder_cache[key][0]:
			del self.__builder_cache[key]

		plan_changed = self.last_change_id
		if key in self.__builder_cache and plan_changed != self.__builder_cache[key][1]:
			del self.__builder_cache[key]

		if key not in self.__builder_cache:
			self.__builder_cache[key] = (island_changed, plan_changed, self.__make_new_builder(building_id, x, y, needs_collector, orientation))
		return self.__builder_cache[key][2]

	def _init_cache(self):
		"""Initialise the cache that knows the last time the buildability of a rectangle may have changed in this area."""
		super(ProductionBuilder, self)._init_cache()
		self.__collector_area_cache = None
		self.__available_squares_cache = {}

	def register_change(self, x, y, purpose, data):
		"""Register the possible buildability change of a rectangle on this island."""
		super(ProductionBuilder, self).register_change(x, y, purpose, data)
		coords = (x, y)
		if coords in self.land_manager.village or (coords not in self.plan and coords not in self.land_manager.coastline):
			return
		self.last_change_id += 1

	def handle_lost_area(self, coords_list):
		"""Handle losing the potential land in the given coordinates list."""
		# remove planned fields that are now impossible
		field_size = Entities.buildings[BUILDINGS.POTATO_FIELD_CLASS].size
		removed_list = []
		for coords, (purpose, _) in self.plan.iteritems():
			if purpose in [BUILDING_PURPOSE.POTATO_FIELD, BUILDING_PURPOSE.PASTURE, BUILDING_PURPOSE.SUGARCANE_FIELD, BUILDING_PURPOSE.TOBACCO_FIELD]:
				rect = Rect.init_from_topleft_and_size_tuples(coords, field_size)
				for field_coords in rect.tuple_iter():
					if field_coords not in self.land_manager.production:
						removed_list.append(coords)
						break

		for coords in removed_list:
			rect = Rect.init_from_topleft_and_size_tuples(coords, field_size)
			for field_coords in rect.tuple_iter():
				self.plan[field_coords] = (BUILDING_PURPOSE.NONE, None)
		self._refresh_unused_fields()
		super(ProductionBuilder, self).handle_lost_area(coords_list)

	def handle_new_area(self):
		"""Handle receiving more land to the production area (this can happen when the village area gives some up)."""
		for coords in self.land_manager.production:
			if coords not in self.plan:
				self.plan[coords] = (BUILDING_PURPOSE.NONE, None)

	collector_building_classes = [BUILDINGS.WAREHOUSE_CLASS, BUILDINGS.STORAGE_CLASS]
	field_building_classes = [BUILDINGS.POTATO_FIELD_CLASS, BUILDINGS.PASTURE_CLASS, BUILDINGS.SUGARCANE_FIELD_CLASS, BUILDINGS.TOBACCO_FIELD_CLASS]
	production_building_classes = set([BUILDINGS.FISHERMAN_CLASS, BUILDINGS.LUMBERJACK_CLASS, BUILDINGS.FARM_CLASS, BUILDINGS.CLAY_PIT_CLASS,
		BUILDINGS.BRICKYARD_CLASS, BUILDINGS.WEAVER_CLASS, BUILDINGS.DISTILLERY_CLASS, BUILDINGS.IRON_MINE_CLASS, BUILDINGS.SMELTERY_CLASS,
		BUILDINGS.TOOLMAKER_CLASS, BUILDINGS.CHARCOAL_BURNER_CLASS, BUILDINGS.TOBACCONIST_CLASS, BUILDINGS.SALT_PONDS_CLASS])

	def add_building(self, building):
		"""Called when a new building is added in the area (the building already exists during the call)."""
		if building.id in self.collector_building_classes:
			self.collector_buildings.append(building)
		elif building.id in self.production_building_classes:
			self.production_buildings.append(building)

		super(ProductionBuilder, self).add_building(building)

	def _handle_lumberjack_removal(self, building):
		"""Release the unused trees around the lumberjack building being removed."""
		used_trees = set()
		for lumberjack_building in self.settlement.buildings_by_id.get(BUILDINGS.LUMBERJACK_CLASS, []):
			if lumberjack_building.worldid == building.worldid:
				continue
			for coords in lumberjack_building.position.get_radius_coordinates(lumberjack_building.radius):
				used_trees.add(coords)

		for coords in building.position.get_radius_coordinates(building.radius):
			if coords not in used_trees and coords in self.plan and self.plan[coords][0] == BUILDING_PURPOSE.TREE:
				self.register_change(coords[0], coords[1], BUILDING_PURPOSE.NONE, None)

	def _handle_farm_removal(self, building):
		"""Handle farm removal by removing planned fields and tearing existing ones that can't be serviced by another farm."""
		unused_fields = set()
		farms = self.settlement.buildings_by_id.get(BUILDINGS.FARM_CLASS, [])
		for coords in building.position.get_radius_coordinates(building.radius):
			if not coords in self.plan:
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
			for x, y in unused_field.position.tuple_iter():
				self.register_change(x, y, BUILDING_PURPOSE.NONE, None)
			Tear(unused_field).execute(self.session)

		# remove the planned but never built fields from the plan
		self._refresh_unused_fields()
		for unused_fields_list in self.unused_fields.itervalues():
			for coords in unused_fields_list:
				position = Rect.init_from_topleft_and_size_tuples(coords, Entities.buildings[BUILDINGS.POTATO_FIELD_CLASS].size)
				if building.position.distance(position) > building.radius:
					continue # it never belonged to the removed building

				used_by_another_farm = False
				for farm in farms:
					if farm.worldid != building.worldid and position.distance(farm.position) <= farm.radius:
						used_by_another_farm = True
						break
				if not used_by_another_farm:
					for x, y in position.tuple_iter():
						self.register_change(x, y, BUILDING_PURPOSE.NONE, None)
		self._refresh_unused_fields()

	def remove_building(self, building):
		"""Called when a building is removed from the area (the building still exists during the call)."""
		if building.id in self.field_building_classes:
			# this can't be handled right now because the building still exists
			Scheduler().add_new_object(Callback(self._refresh_unused_fields), self, run_in = 0)
			Scheduler().add_new_object(Callback(partial(super(ProductionBuilder, self).remove_building, building)), self, run_in = 0)
		elif building.buildable_upon or building.id == BUILDINGS.TRAIL_CLASS:
			pass # don't react to road, trees and ruined tents being destroyed
		else:
			for x, y in building.position.tuple_iter():
				self.register_change(x, y, BUILDING_PURPOSE.NONE, None)

			if building.id in self.collector_building_classes:
				self.collector_buildings.remove(building)
			elif building.id in self.production_building_classes:
				self.production_buildings.remove(building)

			if building.id == BUILDINGS.LUMBERJACK_CLASS:
				self._handle_lumberjack_removal(building)
			elif building.id == BUILDINGS.FARM_CLASS:
				self._handle_farm_removal(building)

			super(ProductionBuilder, self).remove_building(building)

	def manage_production(self):
		"""Pauses and resumes production buildings when they have full input and output inventories."""
		for building in self.production_buildings:
			producer = building.get_component(Producer)
			for production in producer.get_productions():
				if not production.get_produced_res():
					continue
				all_full = True

				# inventory full of the produced resources?
				for resource_id, min_amount in production.get_produced_res().iteritems():
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
		return '%s.PB(%s/%s)' % (self.owner, self.settlement.get_component(NamedComponent).name if hasattr(self, 'settlement') else 'unknown', \
			self.worldid if hasattr(self, 'worldid') else 'none')

decorators.bind_all(ProductionBuilder)
