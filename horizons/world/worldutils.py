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

import os
import bisect
import itertools

from collections import deque

from horizons.constants import UNITS, BUILDINGS, RES, WILD_ANIMAL
from horizons.command.building import Build
from horizons.util.uhdbaccessor import read_savegame_template
from horizons.entities import Entities
from horizons.util.dbreader import DbReader
from horizons.util import Point
from horizons.component.selectablecomponent import SelectableComponent
from horizons.component.storagecomponent import StorageComponent
from horizons.command.unit import CreateUnit

"""
This is used for random features required by world,
that aren't delicate but need to occupy space somewhere.
"""


def toggle_health_for_all_health_instances(world):
	"""Show health bar of every instance with an health component, which isnt selected already"""
	world.health_visible_for_all_health_instances = not world.health_visible_for_all_health_instances
	if world.health_visible_for_all_health_instances:
		for instance in world.session.world.get_health_instances():
			if not instance.get_component(SelectableComponent).selected:
				instance.draw_health()
				world.session.view.add_change_listener(instance.draw_health)
	else:
		for instance in world.session.world.get_health_instances():
			if world.session.view.has_change_listener(instance.draw_health) and not instance.get_component(SelectableComponent).selected:
				instance.draw_health(remove_only=True)
				world.session.view.remove_change_listener(instance.draw_health)

def toggle_translucency(world):
	"""Make certain building types translucent"""
	if not hasattr(world, "_translucent_buildings"):
		world._translucent_buildings = set()

	if not world._translucent_buildings: # no translucent buildings saved => enable
		building_types = world.session.db.get_translucent_buildings()
		add = world._translucent_buildings.add
		from weakref import ref as create_weakref

		for b in world.get_all_buildings():
			if b.id in building_types:
				fife_instance = b._instance
				add( create_weakref(fife_instance) )
				fife_instance.keep_translucency = True
				fife_instance.get2dGfxVisual().setTransparency( BUILDINGS.TRANSPARENCY_VALUE )

	else: # undo translucency
		for inst in world._translucent_buildings:
			try:
				inst().get2dGfxVisual().setTransparency( 0 )
				inst().keep_translucency = False
			except AttributeError:
				pass # obj has been deleted, inst() returned None
		world._translucent_buildings.clear()


def save_map(world, path, prefix):
	map_file = os.path.join(path, prefix + '.sqlite')
	db = DbReader(map_file)
	read_savegame_template(db)
	db('BEGIN')
	for island in world.islands:
		island_name = '%s_island_%d_%d.sqlite' % (prefix, island.origin.x, island.origin.y)
		island_db_path = os.path.join(path, island_name)
		if os.path.exists(island_db_path):
			os.unlink(island_db_path) # the process relies on having an empty file
		db('INSERT INTO island (x, y, file) VALUES(?, ?, ?)', island.origin.x, island.origin.y, 'content/islands/' + island_name)
		island_db = DbReader(island_db_path)
		island.save_map(island_db)
		island_db.close()
	db('COMMIT')
	db.close()


def add_resource_deposits(world, resource_multiplier):
	"""
	Place clay deposits and mountains.

	The algorithm:
	1. calculate the manhattan distance from each island tile to the sea
	2. calculate the value of a tile
	3. calculate the value of an object's location as min(covered tile values)
	4. for each island place a number of clay deposits and mountains
	5. place a number of extra clay deposits and mountains without caring about the island
	* the probability of choosing a resource deposit location is proportional to its value

	@param natural_resource_multiplier: multiply the amount of clay deposits and mountains by this.
	"""

	moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
	ClayDeposit = Entities.buildings[BUILDINGS.CLAY_DEPOSIT]
	Mountain = Entities.buildings[BUILDINGS.MOUNTAIN]
	clay_deposit_locations = []
	mountain_locations = []

	def get_valid_locations(usable_part, island, width, height):
		"""Return a list of all valid locations for a width times height object in the format [(value, (x, y), island), ...]."""
		locations = []
		offsets = list(itertools.product(xrange(width), xrange(height)))
		for x, y in sorted(usable_part):
			min_value = None
			for dx, dy in offsets:
				coords = (x + dx, y + dy)
				if coords in usable_part:
					value = usable_part[coords]
					min_value = value if min_value is None or min_value > value else min_value
				else:
					min_value = None
					break
			if min_value:
				locations.append((1.0 / min_value, (x, y), island))
		return locations

	def place_objects(locations, max_objects, object_class):
		"""Place at most max_objects objects of the given class."""
		if not locations:
			return

		total_sum = [0]
		last_sum = 0
		for value in zip(*locations)[0]:
			last_sum += value
			total_sum.append(last_sum)

		for _unused1 in xrange(max_objects):
			for _unused2 in xrange(7): # try to place the object 7 times
				object_sum = world.session.random.random() * last_sum
				pos = bisect.bisect_left(total_sum, object_sum, 0, len(total_sum) - 2)
				x, y = locations[pos][1]
				if object_class.check_build(world.session, Point(x, y), check_settlement = False):
					Build(object_class, x, y, locations[pos][2], 45 + world.session.random.randint(0, 3) * 90, ownerless = True)(issuer = None)
					break

	for island in world.islands:
		# mark island tiles that are next to the sea
		queue = deque()
		distance = {}
		for (x, y), tile in island.ground_map.iteritems():
			if len(tile.classes) == 1: # could be a shallow to deep water tile
				for dx, dy in moves:
					coords = (x + dx, y + dy)
					if coords in world.water_body and world.water_body[coords] == world.sea_number:
						distance[(x, y)] = 1
						queue.append((x, y, 1))
						break

		# calculate the manhattan distance to the sea
		while queue:
			x, y, dist = queue[0]
			queue.popleft()
			for dx, dy in moves:
				coords = (x + dx, y + dy)
				if coords in distance:
					continue
				if coords in world.water_body and world.water_body[coords] == world.sea_number:
					continue
				distance[coords] = dist + 1
				queue.append((coords[0], coords[1], dist + 1))

		# calculate tiles' values
		usable_part = {}
		for coords, dist in distance.iteritems():
			if coords in island.ground_map and 'constructible' in island.ground_map[coords].classes:
				usable_part[coords] = (dist + 5) ** 2

		# place the local clay deposits
		local_clay_deposit_locations = get_valid_locations(usable_part, island, *ClayDeposit.size)
		clay_deposit_locations.extend(local_clay_deposit_locations)
		local_clay_deposits_base = 0.3 + len(local_clay_deposit_locations) ** 0.7 / 60.0
		num_local_clay_deposits = int(max(0, resource_multiplier * min(3, local_clay_deposits_base + abs(world.session.random.gauss(0, 0.7)))))
		place_objects(local_clay_deposit_locations, num_local_clay_deposits, ClayDeposit)

		# place the local mountains
		local_mountain_locations = get_valid_locations(usable_part, island, *Mountain.size)
		mountain_locations.extend(local_mountain_locations)
		local_mountains_base = 0.1 + len(local_mountain_locations) ** 0.5 / 120.0
		num_local_mountains = int(max(0, resource_multiplier * min(2, local_mountains_base + abs(world.session.random.gauss(0, 0.8)))))
		place_objects(local_mountain_locations, num_local_mountains, Mountain)

	# place some extra clay deposits
	extra_clay_base = len(clay_deposit_locations) ** 0.8 / 400.0
	num_extra_clay_deposits = int(round(max(1, resource_multiplier * min(7, len(world.islands) * 1.0 + 2, extra_clay_base + abs(world.session.random.gauss(0, 1))))))
	place_objects(clay_deposit_locations, num_extra_clay_deposits, ClayDeposit)

	# place some extra mountains
	extra_mountains_base = len(mountain_locations) ** 0.8 / 700.0
	num_extra_mountains = int(round(max(1, resource_multiplier * min(4, len(world.islands) * 0.5 + 2, extra_mountains_base + abs(world.session.random.gauss(0, 0.7))))))
	place_objects(mountain_locations, num_extra_mountains, Mountain)


def add_nature_objects(world, natural_resource_multiplier):
	"""
	Place trees, wild animals, fish deposits, clay deposits, and mountains.

	@param natural_resource_multiplier: multiply the amount of fish deposits, clay deposits, and mountains by this.
	"""

	if not int(world.properties.get('RandomTrees', 1)):
		return

	add_resource_deposits(world, natural_resource_multiplier)
	Tree = Entities.buildings[BUILDINGS.TREE]
	FishDeposit = Entities.buildings[BUILDINGS.FISH_DEPOSIT]
	fish_directions = [(i, j) for i in xrange(-1, 2) for j in xrange(-1, 2)]

	# TODO HACK BAD THING hack the component template to make trees start finished
	Tree.component_templates[1]['ProducerComponent']['start_finished'] = True

	# add trees, wild animals, and fish
	for island in world.islands:
		for (x, y), tile in sorted(island.ground_map.iteritems()):
			# add tree to every nth tile and an animal to one in every M trees
			if world.session.random.randint(0, 2) == 0 and \
			   Tree.check_build(world.session, tile, check_settlement = False):
				building = Build(Tree, x, y, island, 45 + world.session.random.randint(0, 3) * 90, ownerless = True)(issuer = None)
				if world.session.random.randint(0, WILD_ANIMAL.POPUlATION_INIT_RATIO) == 0: # add animal to every nth tree
					CreateUnit(island.worldid, UNITS.WILD_ANIMAL, x, y)(issuer = None)
				if world.session.random.random() > WILD_ANIMAL.FOOD_AVAILABLE_ON_START:
					building.get_component(StorageComponent).inventory.alter(RES.WILDANIMALFOOD, -1)

			if 'coastline' in tile.classes and world.session.random.random() < natural_resource_multiplier / 4.0:
				# try to place fish: from the current position go to a random directions twice
				for (x_dir, y_dir) in world.session.random.sample(fish_directions, 2):
					# move a random amount in both directions
					fish_x = x + x_dir * world.session.random.randint(3, 9)
					fish_y = y + y_dir * world.session.random.randint(3, 9)
					# now we have the location, check if we can build here
					if (fish_x, fish_y) in world.ground_map:
						Build(FishDeposit, fish_x, fish_y, world, 45 + world.session.random.randint(0, 3) * 90, ownerless = True)(issuer = None)

	# TODO HACK BAD THING revert hack so trees don't start finished
	Tree.component_templates[1]['ProducerComponent']['start_finished'] = False


def get_random_possible_ground_unit_position(world):
	"""Returns a position in water, that is not at the border of the world"""
	offset = 2
	while True:
		x = world.session.random.randint(world.min_x + offset, world.max_x - offset)
		y = world.session.random.randint(world.min_y + offset, world.max_y - offset)

		if (x, y) in world.ground_unit_map:
			continue

		for island in world.islands:
			if (x, y) in island.path_nodes.nodes:
				return Point(x, y)

def get_random_possible_ship_position(world):
	"""Returns a position in water, that is not at the border of the world"""
	offset = 2
	while True:
		x = world.session.random.randint(world.min_x + offset, world.max_x - offset)
		y = world.session.random.randint(world.min_y + offset, world.max_y - offset)

		if (x, y) in world.ship_map:
			continue # don't place ship where there is already a ship

		# check if there is an island nearby (check only important coords)
		position_possible = True
		for first_sign in (-1, 0, 1):
			for second_sign in (-1, 0, 1):
				point_to_check = Point( x + offset*first_sign, y + offset*second_sign )
				if world.get_island(point_to_check) is not None:
					position_possible = False
					break
		if not position_possible: # propagate break
			continue # try another coord

		break # all checks successful

	return Point(x, y)

def get_random_possible_coastal_ship_position(world):
	"""Returns a position in water, that is not at the border of the world
	but on the coast of an island"""
	offset = 2
	while True:
		x = world.session.random.randint(world.min_x + offset, world.max_x - offset)
		y = world.session.random.randint(world.min_y + offset, world.max_y - offset)

		if (x, y) in world.ship_map:
			continue # don't place ship where there is already a ship

		result = Point(x, y)
		if world.get_island(result) is not None:
			continue # don't choose a point on an island

		# check if there is an island nearby (check only important coords)
		for first_sign in (-1, 0, 1):
			for second_sign in (-1, 0, 1):
				point_to_check = Point( x + first_sign, y + second_sign )
				if world.get_island(point_to_check) is not None:
					return result

