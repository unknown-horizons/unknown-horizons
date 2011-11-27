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

from horizons.world.resourcehandler import ResourceHandler
from horizons.util.changelistener import metaChangeListenerDecorator
from horizons.gui.tabs import ProductionOverviewTab
from horizons.command.unit import CreateUnit
from horizons.world.production.unitproduction import UnitProduction
from horizons.world.production.producer import Producer, QueueProducer


class BuildingResourceHandler(ResourceHandler):
	"""A Resourcehandler that is also a building.
	This class exists because we keep a list of all buildings, that provide something at the island.
	"""
	def __init__(self, island, **kwargs):
		super(BuildingResourceHandler, self).__init__(island=island, **kwargs)
		self.__init(island)

	def __init(self, island):
		"""
		@param island: the island where the building is located
		"""
		island.provider_buildings.append(self)

	def load(self, db, worldid):
		super(BuildingResourceHandler, self).load(db, worldid)
		# workaround, fetch island from db cause self.island might not be initialised
		location = self.load_location(db, worldid)
		island = location[0]
		self.__init(island)
		self._set_running_costs_to_status()

	def remove(self):
		super(BuildingResourceHandler, self).remove()
		self.island.provider_buildings.remove(self)

	def set_active(self, production=None, active=True):
		if self.has_component(Producer):
			self.get_component(Producer).set_active(production, active)
		# set running costs, if activity status has changed.
		self._set_running_costs_to_status()

	def _set_running_costs_to_status(self):
		if self.running_costs_active():
			if self.has_component(Producer) and not self.get_component(Producer).is_active():
				self.toggle_costs()
		else:
			if self.has_component(Producer) and self.get_component(Producer).is_active():
				self.toggle_costs()
		self._changed()

@metaChangeListenerDecorator("building_production_finished")
class ProducerBuilding(BuildingResourceHandler):
	"""Class for buildings, that produce something.
	Uses BuildingResourceHandler additionally to ResourceHandler, to enable building-specific
	behaviour"""
	tabs = (ProductionOverviewTab,) # don't show inventory, just production (i.e. running costs)

	def __init__(self, start_finished=False, *args, **kwargs):
		super(ProducerBuilding, self).__init__(*args, **kwargs)
		self.add_component(Producer(start_finished=start_finished))

	def add_production(self, production):
		self.get_component(Producer).add_production(production)
		production.add_production_finished_listener(self._production_finished)

	def _production_finished(self, production):
		"""Gets called when a production finishes."""
		produced_res = production.get_produced_res()
		self.on_building_production_finished(produced_res)

	def get_output_blocked_time(self):
		""" gets the amount of time in range [0, 1] the output storage is blocked for the AI """
		return max(production.get_output_blocked_time() for production in self.get_component(Producer).get_productions())

class UnitProducerBuilding(ProducerBuilding):
	"""Class for building that produce units.
	Uses a BuildingResourceHandler additionally to ResourceHandler to enable
	building specific behaviour."""

	# Use UnitProduction instead of normal Production
	production_class = UnitProduction

	def __init__(self, **kwargs):
		super(UnitProducerBuilding, self).__init__(**kwargs)
		self.add_component(QueueProducer())
		self.set_active(active=False)


	def get_production_progress(self):
		"""Returns the current progress of the active production."""
		for production in self._productions.itervalues():
			# Always return first production
			return production.progress
		for production in self._inactive_productions.itervalues():
			# try inactive ones, if no active ones are found
			# this makes e.g. the boatbuilder's progress bar constant when you pause it
			return production.progress
		return 0 # No production available

	def on_queue_element_finished(self, production):
		self.__create_unit()
		super(UnitProducerBuilding, self).on_queue_element_finished(production)

	#----------------------------------------------------------------------
	def __create_unit(self):
		"""Create the produced unit now."""
		productions = self._productions.values()
		for production in productions:
			assert isinstance(production, UnitProduction)
			self.on_building_production_finished(production.get_produced_units())
			for unit, amount in production.get_produced_units().iteritems():
				for i in xrange(0, amount):
					radius = 1
					found_tile = False
					# search for free water tile, and increase search radius if none is found
					while not found_tile:
						for coord in Circle(self.position.center(), radius).tuple_iter():
							point = Point(coord[0], coord[1])
							if self.island.get_tile(point) is None:
								tile = self.session.world.get_tile(point)
								if tile is not None and tile.is_water and coord not in self.session.world.ship_map:
									# execute bypassing the manager, it's simulated on every machine
									CreateUnit(self.owner.worldid, unit, point.x, point.y)(issuer=self.owner)
									found_tile = True
									break
						radius += 1
