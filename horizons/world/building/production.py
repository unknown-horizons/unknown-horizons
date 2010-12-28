# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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
from horizons.util import Circle
from horizons.command.building import Build
from horizons.scheduler import Scheduler
from horizons.constants import BUILDINGS, PRODUCTION


class Farm(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	max_fields_possible = 8 # only for utilisation calculation
	def _update_capacity_utilisation(self):
		"""Farm doesn't acctually produce something, so calculate productivity by the number of fields
		nearby."""
		reach = Circle(self.position.center(), self.radius)
		providers = self.island.get_providers_in_range(reach, reslist=self.get_needed_resources())
		providers = [ p for p in providers if isinstance(p, Field) ]
		self.capacity_utilisation = float(len(providers))/self.max_fields_possible
		# sanity checks for theoretically impossible cases:
		self.capacity_utilisation = min(self.capacity_utilisation, 1.0)
		self.capacity_utilisation = max(self.capacity_utilisation, 0.0)

class Lumberjack(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass

class Weaver(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass

class Distillery(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass

class Hunter(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass

class Fisher(SelectableBuilding, ProducerBuilding, BuildableSingleOnCoast, BasicBuilding):
	pass

class IronRefiner(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass
	
class Smeltery(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass
	
class CharcoalBurning(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass

class Brickyard(SelectableBuilding, CollectingProducerBuilding, BuildableSingle, BasicBuilding):
	pass

class SettlerServiceProvider(SelectableBuilding, ProducerBuilding, BuildableSingle, BasicBuilding):
	"""Class for Churches, School that provide a service-type res for settlers"""
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
		Scheduler().add_new_object(build_cmd, build_cmd, runin=0)

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
			if self.is_active():
				self.set_active(active=False)



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

