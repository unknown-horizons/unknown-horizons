# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

from horizons.util import Callback
from horizons.world.resourcehandler import ResourceHandler
from horizons.world.building.buildingresourcehandler import BuildingResourceHandler
from horizons.world.production.production import Production, SingleUseProduction
from horizons.world.production.unitproduction import UnitProduction
from horizons.constants import PRODUCTION
from horizons.command.unit import CreateUnit
from horizons.scheduler import Scheduler
from horizons.gui.tabs import ProductionOverviewTab

import horizons.main

class Producer(ResourceHandler):
	"""Class for objects, that produce something.
	@param auto_init: bool. If True, the producer automatically adds one production
					  for each production_line.
	"""
	log = logging.getLogger("world.production")

	production_class = Production

	_capacity_utilisation_update_interval = 3.0

	# INIT
	def __init__(self, auto_init=True, **kwargs):
		super(Producer, self).__init__(**kwargs)
		self.__init()
		# add production lines as specified in db.
		if auto_init:
			for prod_line in horizons.main.db("SELECT id FROM production_line WHERE object_id = ? \
			    AND enabled_by_default = 1", self.id):
				self.add_production_by_id(prod_line[0], self.production_class)

	def __init(self):
		self.capacity_utilisation = 0.0 # float from 0.0 to 1.0
		# update capacity util. every 3 seconds
		if hasattr(self, 'select'): # only for selectables
			Scheduler().add_new_object(self._update_capacity_utilisation, self, \
		                   Scheduler().get_ticks(self._capacity_utilisation_update_interval), -1)

	def load(self, db, worldid):
		super(Producer, self).load(db, worldid)
		self.__init()

	def load_production(self, db, worldid):
		return self.production_class.load(db, worldid)

	# INTERFACE
	def add_production(self, production):
		assert isinstance(production, Production)
		self.log.debug('%s: added production line %s', self, production.get_production_line_id())
		production.on_remove = Callback(self.remove_production, production)
		if production.is_paused():
			self._inactive_productions[production.get_production_line_id()] = production
		else:
			self._productions[production.get_production_line_id()] = production
		production.add_change_listener(self._on_production_change, call_listener_now=True)
		self._changed()

	def remove_production(self, production):
		assert isinstance(production, Production)
		super(Producer, self).remove_production(production)

	def finish_production_now(self):
		"""Cheat, makes current production finish right now (and produce the resources).
		Useful to make trees fully grown at game start."""
		for production in self._productions.itervalues():
			production.finish_production_now()

	# PROTECTED METHODS
	def _get_current_state(self):
		"""Returns the current state of the producer. It is the most important
		state of all productions combined. Check the PRODUCTION.STATES constant
		for list of states and their importance."""
		current_state = PRODUCTION.STATES.none
		for production in self._get_productions():
			state = production.get_animating_state()
			if state is not None and current_state < state:
				current_state = state
		return current_state

	def _on_production_change(self):
		"""Makes the instance act according to the producers
		current state"""
		state = self._get_current_state()
		if (state is PRODUCTION.STATES.waiting_for_res or\
			state is PRODUCTION.STATES.paused or\
			state is PRODUCTION.STATES.none):
			self.act("idle", repeating=True)
		elif state is PRODUCTION.STATES.producing:
			self.act("work", repeating=True)
		elif state is PRODUCTION.STATES.inventory_full:
			self.act("idle_full", repeating=True)

	def _update_capacity_utilisation(self):
		"""Update the capacity utilisation value"""
		capacity_used = (self._get_current_state() == PRODUCTION.STATES.producing)
		part = self._capacity_utilisation_update_interval / \
		     PRODUCTION.CAPACITY_UTILISATION_CONSIDERED_SECONDS
		part *= 1 if capacity_used else -1
		self.capacity_utilisation += part
		self.capacity_utilisation = min(self.capacity_utilisation, 1.0)
		self.capacity_utilisation = max(self.capacity_utilisation, 0.0)


class ProducerBuilding(Producer, BuildingResourceHandler):
	"""Class for buildings, that produce something.
	Uses BuildingResourceHandler additionally to ResourceHandler, to enable building-specific
	behaviour"""
	tabs = [ProductionOverviewTab] # don't show inventory, just production (i.e. running costs)

	def add_production(self, production):
		super(ProducerBuilding, self).add_production(production)
		#production.on_production_finished = ...display_sth..


class QueueProducer(Producer):
	"""The QueueProducer stores all productions in a queue and runs them one
	by one. """

	production_class = SingleUseProduction

	def __init__(self, **kwargs):
		super(QueueProducer, self).__init__(auto_init=False, **kwargs)
		self.__init()

	def __init(self):
		self.production_queue = []

	def load(self, db, worldid):
		super(QueueProducer, self).load(db, worldid)
		self.__init()

	def add_production_by_id(self, production_line_id, production_class = Production):
		"""Convenience method.
		@param production_line_id: Production line from db
		@param production_class: Subclass of Production that does the production. If the object
		                         has a production_class-member, this will be used instead.
		"""
		#print "Add production"
		self.production_queue.append(production_line_id)
		self.start_next_production()

	def check_next_production_startable(self):
		# See if we can start the next production,  this only works if the current
		# production is done
		#print "Check production"
		state = self._get_current_state()
		return (state is PRODUCTION.STATES.done or\
				state is PRODUCTION.STATES.none) and\
			   (len(self.production_queue) > 0)

	def on_production_finished(self, production_line):
		"""Callback used for the SingleUseProduction"""
		self.remove_production(production_line)
		Scheduler().add_new_object(self.start_next_production, self)

	def start_next_production(self):
		"""Starts the next production that is in the queue, if there is one."""
		#print "Start next?"
		if self.check_next_production_startable():
			#print "yes"
			self.set_active(active=True)
			self._productions.clear() # Make sure we only have one production active
			production_line_id = self.production_queue.pop(0)
			self.add_production(self.production_class(inventory=self.inventory, prod_line_id=production_line_id, callback=self.on_production_finished))
		else:
			self.set_active(active=False)

class UnitProducerBuilding(QueueProducer, BuildingResourceHandler):
	"""Class for building that produce units.
	Uses a BuildingResourceHandler additionally to ResourceHandler to enable
	building specific behaviour."""

	# Use UnitProduction instead of normal Production
	production_class = UnitProduction

	unit_placement_radius = 3 # Radius in which the producer can  setup a new unit

	def __init__(self, **kwargs):
		super(UnitProducerBuilding, self).__init__(**kwargs)
		self.set_active(active=False)

	def get_production_progress(self):
		"""Returns the current progress of the active production."""
		for production in self._productions.values():
			# Always return first production
			return production.progress
		return 0 # No production available

	def on_production_finished(self, production_line):
		self.__create_unit()
		super(UnitProducerBuilding, self).on_production_finished(production_line)

	#----------------------------------------------------------------------
	def __create_unit(self):
		"""Create the produced unit now."""
		productions = self._productions.values()
		for production in productions:
			assert isinstance(production, UnitProduction)
			for unit, amount in production.get_produced_units().iteritems():
				found_tile = False
				radius = self.unit_placement_radius
				# search for free water tile, and in increase search radius if none is found
				while not found_tile:
					for tile in self.session.world.get_tiles_in_radius(self.position.center(), radius):
						if tile.is_water:
							found_tile = True
							for i in xrange(0, amount):
								print "created unit", unit, "amount:", amount
								CreateUnit(self.owner.getId(), unit, tile.x, tile.y).execute(self.session)
							break
					radius += 1

