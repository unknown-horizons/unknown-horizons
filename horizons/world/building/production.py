# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

import horizons.main

from horizons.world.building.collectingproducerbuilding import CollectingProducerBuilding
from horizons.world.production.producer import ProducerBuilding
from horizons.world.building.building import BasicBuilding, SelectableBuilding
from horizons.world.building.buildable import BuildableSingle, BuildableSingleOnCoast, BuildableSingleOnDeposit
from horizons.world.building.nature import Field
from horizons.util import Rect, Circle
from horizons.util.shapes.radiusshape import RadiusShape, RadiusRect
from horizons.command.building import Build
from horizons.scheduler import Scheduler
from horizons.constants import BUILDINGS, PRODUCTION, RES, GAME_SPEED
from horizons.gui.tabs import ProductionOverviewTab


class Farm(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	max_fields_possible = 8 # only for utilisation calculation
	tabs = (ProductionOverviewTab,)

	def _get_providers(self):
		reach = RadiusRect(self.position, self.radius)
		providers = self.island.get_providers_in_range(reach, reslist=self.get_needed_resources())
		return [provider for provider in providers if isinstance(provider, Field)]

	def _update_capacity_utilisation(self):
		"""Farm doesn't acctually produce something, so calculate productivity by the number of fields
		nearby."""
		self.capacity_utilisation = float(len(self._get_providers())) / self.max_fields_possible
		# sanity checks for theoretically impossible cases:
		self.capacity_utilisation = min(self.capacity_utilisation, 1.0)
		self.capacity_utilisation = max(self.capacity_utilisation, 0.0)

	def get_expected_production_level(self, resource_id):
		fields = 0
		for provider in self._get_providers():
			if resource_id == RES.FOOD_ID and provider.id == BUILDINGS.POTATO_FIELD_CLASS:
				fields += 1
			elif resource_id == RES.WOOL_ID and provider.id == BUILDINGS.PASTURE_CLASS:
				fields += 1
			elif resource_id == RES.SUGAR_ID and provider.id == BUILDINGS.SUGARCANE_FIELD_CLASS:
				fields += 1
		return self.owner.virtual_farm.get_expected_production_level(resource_id, fields)

class Lumberjack(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	def get_expected_production_level(self, resource_id):
		if resource_id != RES.BOARDS_ID:
			return None
		production = [production for production in self._get_productions()][0]
		amount = 0
		for sub_amount in production._prod_line.produced_res.itervalues():
			amount += sub_amount
		return float(amount) / production._prod_line.time / GAME_SPEED.TICKS_PER_SECOND

class Weaver(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass

class Distillery(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass

class Hunter(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass

class IronRefiner(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass

class Smeltery(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass

class CharcoalBurning(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass

class Brickyard(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass

class Fisher(SelectableBuilding, CollectingProducerBuilding, BuildableSingleOnCoast, BasicBuilding):

	@classmethod
	def _do_select(cls, renderer, position, world, settlement):
		# Don't call super here, because we don't want to highlight the island
		# only fish deposits
		island = world.get_island(position.center())
		for building in world.get_providers_in_range(RadiusShape(position, cls.radius), res=RES.FISH_ID):
			renderer.addColored(building._instance, *cls.selection_color)
			cls._selected_tiles.append(building)

	def deselect(self):
		# TODO: find out if deselect_building should be dropped in favor of deselect
		# since the latter is faster, and the specific deselecting of the first doesn't
		# seem to be needed anywhere
		# if so, this can be removed
		self.deselect_building(self.session)
		renderer = self.session.view.renderer['InstanceRenderer']
		renderer.removeOutlined(self._instance)

	@classmethod
	def deselect_building(cls, session):
		"""@see select_building,
		@return list of tiles that were deselected."""
		remove_colored = session.view.renderer['InstanceRenderer'].removeColored
		for tile in cls._selected_tiles:
			remove_colored(tile._instance)
		# this acctually means SelectableBuilding._selected_tiles = []
		# writing self._selected_tiles = [] however creates a new variable in this instance,
		# which isn't what we want. Therefore this workaround:
		while cls._selected_tiles:
			cls._selected_tiles.pop()

	def get_expected_production_level(self, resource_id):
		return self.owner.virtual_fisher.get_expected_production_level(resource_id)

class SettlerServiceProvider(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	"""Class for Churches, School that provide a service-type res for settlers.
	Also provides collectors for buildings that consume resources (tavern)."""
	pass

class Mine(SelectableBuilding, ProducerBuilding, BuildableSingleOnDeposit, BasicBuilding):
	def __init__(self, inventory, deposit_class, *args, **kwargs):
		"""
		@param inventory: inventory dump of deposit (collected by get_prebuild_data())
		@param deposit_class: class num of deposit for later reconstruction (collected by get_prebuild_data())
		"""
		# needs to be inited before super(), since that will call the _on_production_changed hook
		super(Mine, self).__init__(*args, **kwargs)
		self.__init(deposit_class, mine_empty_msg_shown=False)
		for res, amount in inventory.iteritems():
			self.inventory.alter(res, amount)

	def __init(self, deposit_class, mine_empty_msg_shown):
		self.__deposit_class = deposit_class
		self._mine_empty_msg_shown = mine_empty_msg_shown

		# setup loading area
		# TODO: for now we assume that a mine building is 5x5 with a 3x1 entry on 1 side
		#       this needs to be generalised, possibly by defining the loading tiles in the db
		pos = self.position
		if self.rotation == 45:
			self.loading_area = Rect.init_from_topleft_and_size(pos.origin.x, pos.origin.y + 1, 0, 2)
		elif self.rotation == 135:
			self.loading_area = Rect.init_from_topleft_and_size(pos.origin.x + 1, pos.origin.y + pos.height - 1, 2, 0)
		elif self.rotation == 225:
			self.loading_area = Rect.init_from_topleft_and_size(pos.origin.x + pos.width -1, pos.origin.y + 1, 0, 2)
		elif self.rotation == 315:
			self.loading_area = Rect.init_from_topleft_and_size(pos.origin.x + 1, pos.origin.y, 2, 0)
		else:
			assert False

	@classmethod
	def get_prebuild_data(cls, session, position):
		"""Returns dict containing inventory of deposit, which is needed for the mine build"""
		deposit = session.world.get_building(position.center())
		data = {}
		data["inventory"] = deposit.inventory.get_dump()
		data["deposit_class"] = deposit.id
		return data

	def remove(self):
		# build the deposit back here after remove() is finished
		deposit_build_data = { 'inventory' : self.inventory.get_dump() }
		build_cmd = Build(self.__deposit_class, self.position.origin.x, self.position.origin.y, \
		                  self.island, ownerless=True, data = deposit_build_data)
		Scheduler().add_new_object(build_cmd, build_cmd, run_in=0)

		super(Mine, self).remove()

	def save(self, db):
		super(Mine, self).save(db)
		db("INSERT INTO mine(rowid, deposit_class, mine_empty_msg_shown) VALUES(?, ?, ?)", \
		   self.worldid, self.__deposit_class, self._mine_empty_msg_shown)

	def load(self, db, worldid):
		super(Mine, self).load(db, worldid)
		deposit_class, mine_empty_msg_shown = \
		             db("SELECT deposit_class, mine_empty_msg_shown FROM mine WHERE rowid = ?", worldid)[0]
		self.__init(deposit_class, mine_empty_msg_shown)

	def _on_production_change(self):
		super(ProducerBuilding, self)._on_production_change()
		if self._get_current_state() == PRODUCTION.STATES.waiting_for_res and \
		   (hasattr(self, "_mine_empty_msg_shown") and \
		    not self._mine_empty_msg_shown):
			# all resources are gone from the mine.
			self.session.ingame_gui.message_widget.add(self.position.center().x, \
			                                           self.position.center().y, 'MINE_EMPTY')
			self._mine_empty_msg_shown = True
			if self.is_active():
				self.set_active(active=False)

	def set_active(self, production=None, active=True):
		super(Mine, self).set_active(production, active)
		if active and self._get_current_state() == PRODUCTION.STATES.waiting_for_res:
			# don't allow reactivating a mine that's already empty
			# we can't check for this before changing activity, because the state is paused
			# before. Therefore we have to react here and disable the mine again.
			self.set_active(production, active=False)

""" AnimalFarm is not used for now (code may not work anymore)

class AnimalFarm(SelectableBuilding, CollectingProducerBuilding, BuildableSingleWithSurrounding, BasicBuilding):
	_surroundingBuildingClass = 18
	"" This class builds pasturage in the radius automatically,
	so that farm animals can graze there ""

	def __init__(self, **kwargs):
		super(AnimalFarm, self).__init__(**kwargs)

	def create_collector(self):
		self.animals = []

		# NOTE: animals have to be created before the AnimalCollector
		for (animal, number) in horizons.main.db("SELECT unit_id, count FROM data.animals \
		                                    WHERE building_id = ?", self.id):
			for i in xrange(0, number):
				Entities.units[animal](self)

		super(AnimalFarm, self).create_collector()

	def save(self, db):
		super(AnimalFarm, self).save(db)
		for animal in self.animals:
			animal.save(db)

	def load(self, db, worldid):
		super(AnimalFarm, self).load(db, worldid)
		self.animals = []

	def remove(self):
		while len(self.animals) > 0:
			self.animals[0].remove()
		super(AnimalFarm, self).remove()
"""

