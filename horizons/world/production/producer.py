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

import logging

from horizons.util.changelistener import metaChangeListenerDecorator
from horizons.world.resourcehandler import ResourceHandler
from horizons.world.building.buildingresourcehandler import BuildingResourceHandler
from horizons.world.production.productionline import ProductionLine
from horizons.world.production.production import Production, SingleUseProduction
from horizons.world.production.unitproduction import UnitProduction
from horizons.constants import PRODUCTION
from horizons.command.unit import CreateUnit
from horizons.scheduler import Scheduler
from horizons.gui.tabs import ProductionOverviewTab
from horizons.util.shapes.circle import Circle
from horizons.util.shapes.point import Point
from horizons.world.status import ProductivityLowStatus, DecommissionedStatus, InventoryFullStatus

class Producer(ResourceHandler):
	"""Class for objects, that produce something.
	@param auto_init: bool. If True, the producer automatically adds one production
					  for each production_line.
	"""
	log = logging.getLogger("world.production")

	production_class = Production

	# INIT
	def __init__(self, auto_init=True, start_finished=False, **kwargs):
		super(Producer, self).__init__(**kwargs)
		# add production lines as specified in db.
		if auto_init:
			for prod_line in self.session.db("SELECT id FROM production_line WHERE object_id = ? \
			    AND enabled_by_default = 1", self.id):
				# for abeaumont patch: // NOTE: this would now also be deprecated -- totycro, 11/2011
				#self.add_production_by_id(prod_line[0], self.worldid, self.production_class)
				self.add_production_by_id(prod_line[0], start_finished=start_finished)

	@property
	def capacity_utilisation(self):
		total = 0
		productions = self.get_productions()
		if not productions:
			return 0 # catch the border case, else there'll be a div by 0
		for production in productions:
			state_history = production.get_state_history_times(False)
			total += state_history[PRODUCTION.STATES.producing.index]
		return total / len(productions)

	def capacity_utilisation_below(self, limit):
		"""Returns whether the capacity utilisation is below a value.
		It is equivalent to "foo.capacity_utilisation <= value, but faster."""
		# idea: retrieve the value, then check how long it has to take until the limit
		# can be reached (from both sides). Within this timespan, don't check again.
		cur_tick = Scheduler().cur_tick
		if not hasattr(self, "_old_capacity_utilisation") or \
		   self._old_capacity_utilisation[0] < cur_tick or \
		   self._old_capacity_utilisation[1] !=  limit:
			capac = self.capacity_utilisation
			diff = abs(limit - capac)
			# all those values are relative values, so we can just do this:
			interval = diff * PRODUCTION.STATISTICAL_WINDOW
			self._old_capacity_utilisation = (cur_tick + interval, # expiration date
			                                  limit, capac < limit )
		return self._old_capacity_utilisation[2]


	def load(self, db, worldid):
		super(Producer, self).load(db, worldid)

	def load_production(self, db, worldid):
		return self.production_class.load(db, worldid)

	# INTERFACE
	def add_production(self, production):
		assert isinstance(production, Production)
		self.log.debug('%s: added production line %s', self, production.get_production_line_id())
		if production.is_paused():
			self._inactive_productions[production.get_production_line_id()] = production
		else:
			self._productions[production.get_production_line_id()] = production
		production.add_change_listener(self._on_production_change, call_listener_now=True)
		self._changed()

	def finish_production_now(self):
		"""Cheat, makes current production finish right now (and produce the resources).
		Useful to make trees fully grown at game start."""
		for production in self._productions.itervalues():
			production.finish_production_now()

	def alter_production_time(self, modifier, prod_line_id=None):
		"""Multiplies the original production time of all production lines by modifier
		@param modifier: a numeric value
		@param prod_line_id: id of production line to alter. None means every production line"""
		if prod_line_id is None:
			for production in self.get_productions():
				production.alter_production_time(modifier)
		else:
			self._get_production(prod_line_id).alter_production_time(modifier)

	# PROTECTED METHODS
	def _get_current_state(self):
		"""Returns the current state of the producer. It is the most important
		state of all productions combined. Check the PRODUCTION.STATES constant
		for list of states and their importance."""
		current_state = PRODUCTION.STATES.none
		for production in self.get_productions():
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

		if self.has_status_icon:
			full = state is PRODUCTION.STATES.inventory_full
			if full and not hasattr(self, "_producer_status_icon"):
				affected_res = set() # find them:
				for prod in self.get_productions():
					affected_res = affected_res.union( prod.get_unstorable_produced_res() )
				self._producer_status_icon = InventoryFullStatus(affected_res)
				self._registered_status_icons.append( self._producer_status_icon )

			if not full and hasattr(self, "_producer_status_icon"):
				self._registered_status_icons.remove( self._producer_status_icon )
				del self._producer_status_icon

	def get_status_icons(self):
		l = super(Producer, self).get_status_icons()
		if self.capacity_utilisation_below(ProductivityLowStatus.threshold):
			l.append( ProductivityLowStatus() )
		if not self.is_active():
			l.append( DecommissionedStatus() )
		return l

@metaChangeListenerDecorator("building_production_finished")
class ProducerBuilding(Producer, BuildingResourceHandler):
	"""Class for buildings, that produce something.
	Uses BuildingResourceHandler additionally to ResourceHandler, to enable building-specific
	behaviour"""
	tabs = (ProductionOverviewTab,) # don't show inventory, just production (i.e. running costs)

	def add_production(self, production):
		super(ProducerBuilding, self).add_production(production)
		production.add_production_finished_listener(self._production_finished)

	def _production_finished(self, production):
		"""Gets called when a production finishes."""
		produced_res = production.get_produced_res()
		self.on_building_production_finished(produced_res)

	def get_output_blocked_time(self):
		""" gets the amount of time in range [0, 1] the output storage is blocked for the AI """
		return max(production.get_output_blocked_time() for production in self.get_productions())

class QueueProducer(Producer):
	"""The QueueProducer stores all productions in a queue and runs them one
	by one. """

	production_class = SingleUseProduction

	def __init__(self, **kwargs):
		super(QueueProducer, self).__init__(auto_init=False, **kwargs)
		self.__init()

	def __init(self):
		self.production_queue = [] # queue of production line ids

	def save(self, db):
		super(QueueProducer, self).save(db)
		for i in enumerate(self.production_queue):
			position, prod_line_id = i
			db("INSERT INTO production_queue (object, position, production_line_id) VALUES(?, ?, ?)",
			   self.worldid, position, prod_line_id)

	def load(self, db, worldid):
		super(QueueProducer, self).load(db, worldid)
		self.__init()
		for (prod_line_id,) in db("SELECT production_line_id FROM production_queue WHERE object = ? ORDER by position", worldid):
			self.production_queue.append(prod_line_id)

	def add_production_by_id(self, production_line_id):
		"""Convenience method.
		@param production_line_id: Production line from db
		"""
		self.production_queue.append(production_line_id)
		if not self.is_active():
			self.start_next_production()

	def load_production(self, db, worldid):
		prod = self.production_class.load(db, worldid)
		prod.add_production_finished_listener(self.on_queue_element_finished)
		return prod

	def check_next_production_startable(self):
		# See if we can start the next production,  this only works if the current
		# production is done
		#print "Check production"
		state = self._get_current_state()
		return (state is PRODUCTION.STATES.done or\
				state is PRODUCTION.STATES.none or\
		        state is PRODUCTION.STATES.paused) and\
			   (len(self.production_queue) > 0)

	def on_queue_element_finished(self, production):
		"""Callback used for the SingleUseProduction"""
		self.remove_production(production)
		Scheduler().add_new_object(self.start_next_production, self)

	def start_next_production(self):
		"""Starts the next production that is in the queue, if there is one."""
		if self.check_next_production_startable():
			self.set_active(active=True)
			self._productions.clear() # Make sure we only have one production active
			production_line_id = self.production_queue.pop(0)
			owner_inventory = self._get_owner_inventory()
			prod = self.production_class(inventory=self.inventory, owner_inventory=owner_inventory, prod_line_id=production_line_id)
			prod.add_production_finished_listener(self.on_queue_element_finished)
			self.add_production( prod )
		else:
			self.set_active(active=False)

	def cancel_all_productions(self):
		self.production_queue = []
		self.cancel_current_production()

	def cancel_current_production(self):
		"""Cancels the current production and proceeds to the next one, if there is one"""
		# Remove current productions, loose all progress and resources
		for production in self._productions.copy().itervalues():
			self.remove_production(production)
		for production in self._inactive_productions.copy().itervalues():
			self.remove_production(production)
		if self.production_queue:
			self.start_next_production()
		else:
			self.set_active(active=False)

	def remove_from_queue(self, index):
		"""Remove the index'th element from the queue. First element is 0"""
		self.production_queue.pop(index)
		self._changed()

class UnitProducerBuilding(QueueProducer, ProducerBuilding):
	"""Class for building that produce units.
	Uses a BuildingResourceHandler additionally to ResourceHandler to enable
	building specific behaviour."""

	# Use UnitProduction instead of normal Production
	production_class = UnitProduction

	def __init__(self, **kwargs):
		super(UnitProducerBuilding, self).__init__(**kwargs)
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

	def get_unit_production_queue(self):
		"""Returns a list unit type ids that are going to be produced.
		Does not include the currently produced unit. List is in order."""
		queue = []
		for prod_line_id in self.production_queue:
			prod_line = ProductionLine.get_const_production_line(prod_line_id)
			units = prod_line.unit_production.keys()
			if len(units) > 1:
				print 'WARNING: unit production system has been designed for 1 type per order'
			queue.append(units[0])
		return queue

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
