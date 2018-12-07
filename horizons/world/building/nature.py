from horizons.constants import BUILDINGS, LAYERS
from horizons.scheduler import Scheduler
from horizons.world.building.buildable import BuildableRect, BuildableSingleEverywhere
from horizons.world.building.building import BasicBuilding
from horizons.world.building.buildingresourcehandler import BuildingResourceHandler
from horizons.world.production.producer import Producer

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


class NatureBuilding(BuildableRect, BasicBuilding):
	"""Class for objects that are part of the environment, the nature"""
	walkable = True
	layer = LAYERS.OBJECTS


class NatureBuildingResourceHandler(BuildingResourceHandler, NatureBuilding):
	# sorry, but this class is to be removed soon anyway
	pass


class Field(NatureBuildingResourceHandler):
	walkable = False
	layer = LAYERS.OBJECTS

	def initialize(self, **kwargs):
		super().initialize(**kwargs)

		if self.owner.is_local_player:
			# make sure to have a farm nearby when we can reasonably assume that the crops are fully grown
			prod_comp = self.get_component(Producer)
			productions = prod_comp.get_productions()
			if not productions:
				print("Warning: Field is assumed to always produce, but doesn't.", self)
			else:
				run_in = Scheduler().get_ticks(productions[0].get_production_time())
				Scheduler().add_new_object(self._check_covered_by_farm, self, run_in=run_in)

	def _check_covered_by_farm(self):
		"""Warn in case there is no farm nearby to cultivate the field"""
		farm_in_range = any((farm.position.distance(self.position) <= farm.radius) for farm in
		                     self.settlement.buildings_by_id[BUILDINGS.FARM])
		if not farm_in_range and self.owner.is_local_player:
			pos = self.position.origin
			self.session.ingame_gui.message_widget.add(point=pos, string_id="FIELD_NEEDS_FARM",
			                                           check_duplicate=True)


class Tree(NatureBuildingResourceHandler):
	buildable_upon = True
	layer = LAYERS.OBJECTS


class ResourceDeposit(NatureBuilding):
	"""Class for stuff like clay deposits."""
	tearable = False
	layer = LAYERS.OBJECTS
	walkable = False


class Fish(BuildableSingleEverywhere, BuildingResourceHandler, BasicBuilding):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.last_usage_tick = -1000000 # a long time ago

		# Make the fish run at different speeds
		multiplier = 0.7 + self.session.random.random() * 0.6
		self._instance.setTimeMultiplier(multiplier)

	def load(self, db, worldid):
		super().load(db, worldid)
		self.last_usage_tick = db.get_last_fish_usage_tick(worldid)

	def save(self, db):
		super().save(db)
		translated_tick = self.last_usage_tick - Scheduler().cur_tick # pre-translate for the loading process
		db("INSERT INTO fish_data(rowid, last_usage_tick) VALUES(?, ?)", self.worldid, translated_tick)

	def remove_incoming_collector(self, collector):
		super().remove_incoming_collector(collector)
		self.last_usage_tick = Scheduler().cur_tick


class Ambient(NatureBuilding):
	"""Class for ambient graphics such as rocks and flowers."""
	buildable_upon = True
	layer = LAYERS.OBJECTS
