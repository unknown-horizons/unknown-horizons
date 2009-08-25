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
from horizons.constants import PRODUCTION_STATES

import horizons.main

class Producer(ResourceHandler):
	"""Class for objects, that produce something.
	@param auto_init: bool. If True, the producer automatically adds one production
					  for each production_line.
	"""
	log = logging.getLogger("world.production")

	production_class = Production

	def __init__(self, auto_init=True, **kwargs):
		super(Producer, self).__init__(**kwargs)
		self.__init()
		# add production lines as specified in db.
		if auto_init:
			for prod_line in horizons.main.db("SELECT id FROM production_line WHERE object_id = ? \
			    AND enabled_by_default = 1", self.id):
				self.add_production_by_id(prod_line[0], self.production_class)

	def __init(self):
		pass

	def add_production(self, production):
		assert isinstance(production, Production)
		self.log.debug('Producer %s: added production line %s', self.getId(), \
									 production.get_production_line_id())
		production.on_remove = Callback(self.remove_production, production)
		self._productions[production.get_production_line_id()] = production
		production.add_change_listener(self.on_production_change, call_listener_now=True)
		self._changed()

	def load_production(self, db, worldid):
		return self.production_class.load(db, worldid)

	def _get_current_state(self):
		"""Returns the current state of the producer. It is the most important
		state of all productions combined. Check the PRODUCTION_STATES constant
		for list of states and their importance."""
		current_state = PRODUCTION_STATES.none
		for production in self._get_productions():
			state = production.get_animating_state()
			if state is not None and current_state < state:
				current_state = state
		return current_state

	def on_production_change(self):
		"""Makes the instance act according to the producers
		current state"""
		state = self._get_current_state()
		if (state is PRODUCTION_STATES.waiting_for_res or\
			state is PRODUCTION_STATES.paused or\
			state is PRODUCTION_STATES.none):
			self.act("idle", repeating=True)
		elif state is PRODUCTION_STATES.producing:
			self.act("work", repeating=True)
		elif state is PRODUCTION_STATES.inventory_full:
			self.act("idle_full", repeating=True)

	def remove_production(self, production):
		assert isinstance(production, Production)
		production.remove_change_listener(self.on_production_change)
		super(Producer, self).remove_production(production)

	def finish_production_now(self):
		"""Cheat, makes current production finish right now (and produce the resources).
		Useful to make trees fully grown at game start."""
		for production in self._productions.itervalues():
			production.finish_production_now()

class ProducerBuilding(Producer, BuildingResourceHandler):
	"""Class for buildings, that produce something.
	Uses BuildingResourceHandler additionally to ResourceHandler, to enable building-specific
	behaviour"""
	pass


class QueueProducer(Producer):
	"""The QueueProducer stores all productions in a queue and runs them one
	by one. """

	production_class = SingleUseProduction

	def __init__(self, **kwargs):
		#ResourceHandler.__init__(self, **kwargs)
		super(QueueProducer, self).__init__(auto_init=False, **kwargs)
		self.production_queue = []

	def add_production_by_id(self, production_line_id, production_class = Production):
		"""Convenience method.
		@param production_line_id: Production line from db
		@param production_class: Subclass of Production that does the production. If the object
		                         has a production_class-member, this will be used instead.
		"""
		print "Add production"
		self.production_queue.append(production_line_id)
		self.start_next_production()


	def check_next_production_startable(self):
		# See if we can start the next production,  this only works if the current
		# production is done
		print "Check production"
		state = self._get_current_state()
		return (state is PRODUCTION_STATES.done or\
				state is PRODUCTION_STATES.none) and\
			   (len(self.production_queue) > 0)


	def on_production_finished(self):
		"""Callback used for the SingleUseProduction"""
		self.start_next_production()


	def start_next_production(self):
		"""Starts the next production that is in the queue, if there is one."""
		print "Start next?"
		if self.check_next_production_startable():
			print "yes"
			self._productions.clear() # Make sure we only have one production active
			production_line_id = self.production_queue.pop(0)
			self.add_production(self.production_class(inventory=self.inventory, prod_line_id=production_line_id, callback=self.on_production_finished))


class UnitProducerBuilding(QueueProducer, BuildingResourceHandler):
	"""Class for building that produce units.
	Uses a BuildingResourceHandler additionally to ResourceHandler to enable
	building specific behaviour."""

	# Use UnitProduction instead of normal Production
	production_class = UnitProduction


	def __init__(self, **kwargs):
		super(UnitProducerBuilding, self).__init__(**kwargs)

	def get_production_progress(self):
		"""Returns the current progress of the active production."""
		for production in self._productions.values():
			# Always return first production
			return production.progress
		return 0 # No production available