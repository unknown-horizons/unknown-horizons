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

from horizons.world.building.building import BasicBuilding
from horizons.world.building.buildable import BuildableRect, BuildableSingleEverywhere
from horizons.world.building.buildingresourcehandler import BuildingResourceHandler
from horizons.entities import Entities
from horizons.scheduler import Scheduler
from horizons.constants import LAYERS, BUILDINGS
from horizons.world.production.producer import Producer

class NatureBuilding(BuildableRect, BasicBuilding):
	"""Class for objects that are part of the environment, the nature"""
	walkable = True
	layer = LAYERS.OBJECTS

	def __init__(self, **kwargs):
		super(NatureBuilding, self).__init__(**kwargs)

class NatureBuildingResourceHandler(BuildingResourceHandler, NatureBuilding):
	# sorry, but this class is to be removed soon anyway
	pass

class Field(NatureBuildingResourceHandler):
	walkable = False
	layer = LAYERS.FIELDS

	def initialize(self, **kwargs):
		super(Field, self).initialize( ** kwargs)

		if self.owner.is_local_player:
			# make sure to have a farm nearby when we can reasonably assume that the crops are fully grown
			prod_comp = self.get_component(Producer)
			productions = prod_comp.get_productions()
			if not productions:
				print "Warning: Field is assumed to always produce, but doesn't.", self
			else:
				run_in = Scheduler().get_ticks(productions[0].get_production_time())
				Scheduler().add_new_object(self._check_covered_by_farm, self, run_in=run_in)

	def _check_covered_by_farm(self):
		"""Warn in case there is no farm nearby to cultivate the field"""
		farm_in_range = any( (farm.position.distance( self.position ) <= farm.radius) for farm in
		                     self.settlement.buildings_by_id[ BUILDINGS.FARM ] )
		if not farm_in_range and self.owner.is_local_player:
			pos = self.position.origin
			self.session.ingame_gui.message_widget.add(point=pos, string_id="FIELD_NEEDS_FARM",
			                                           check_duplicate=True)

class AnimalField(Field):
	walkable = False
	def create_collector(self):
		self.animals = []
		for (animal, number) in self.session.db("SELECT unit_id, count FROM animals \
		                                    WHERE building_id = ?", self.id):
			for i in xrange(0, number):
				unit = Entities.units[animal](self, session=self.session)
				unit.initialize()
		super(AnimalField, self).create_collector()

	def remove(self):
		while self.animals:
			self.animals[0].cancel(continue_action=lambda : 42) # don't continue
			self.animals[0].remove()
		super(AnimalField, self).remove()

	def save(self, db):
		super(AnimalField, self).save(db)
		for animal in self.animals:
			animal.save(db)

	def load(self, db, worldid):
		super(AnimalField, self).load(db, worldid)
		self.animals = []
		# units are loaded separatly

class Tree(NatureBuildingResourceHandler):
	buildable_upon = True
	layer = LAYERS.OBJECTS

class ResourceDeposit(NatureBuilding):
	"""Class for stuff like clay deposits."""
	tearable = False
	layer = LAYERS.OBJECTS
	walkable = False

	def __init__(self, *args, **kwargs):
		super(ResourceDeposit, self).__init__(*args, **kwargs)

class Fish(BuildableSingleEverywhere, BuildingResourceHandler, BasicBuilding):

	def __init__(self, *args, **kwargs):
		super(Fish,  self).__init__(*args, **kwargs)

		# Make the fish run at different speeds
		multiplier =  0.7 + self.session.random.random() * 0.6
		self._instance.setTimeMultiplier(multiplier)



