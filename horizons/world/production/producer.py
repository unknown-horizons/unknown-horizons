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
from horizons.world.production.production import Production, SingleUseProduction
from horizons.constants import PRODUCTION
from horizons.scheduler import Scheduler
from horizons.util.shapes.circle import Circle
from horizons.util.shapes.point import Point
from horizons.world.component.storagecomponent import StorageComponent
from horizons.world.status import ProductivityLowStatus, DecommissionedStatus
from horizons.world.component import Component

class Producer(Component):
	"""Class for objects, that produce something.
	@param auto_init: bool. If True, the producer automatically adds one production
					  for each production_line.
	"""
	log = logging.getLogger("world.production")

	NAME = "producer"

	production_class = Production

	# INIT
	def __init__(self, auto_init=True, **kwargs):
		super(Producer, self).__init__(**kwargs)
		self.__auto_init = auto_init

	def initialize(self):
		# we store productions in 2 dicts, one for the active ones, and one for the inactive ones.
		# the inactive ones won't get considered for needed_resources and such.
		# the production_line id is the key in the dict (=> a building must not have two identical
		# production lines)
		self._productions = {}
		self._inactive_productions = {}
		# add production lines as specified in db.
		if self.__auto_init:
			for prod_line in self.instance.session.db("SELECT id FROM production_line WHERE object_id = ? \
			    AND enabled_by_default = 1", self.instance.id):
				# for abeaumont patch:
				#self.add_production_by_id(prod_line[0], self.worldid, self.production_class)
				self.add_production_by_id(prod_line[0], self.production_class)


	def add_production_by_id(self, production_line_id, production_class = Production):
		"""Convenience method.
		@param production_line_id: Production line from db
		@param production_class: Subclass of Production that does the production. If the object
		                         has a production_class-member, this will be used instead.
		"""
		if hasattr(self, "production_class"):
			production_class = self.production_class
		owner_inventory = self.instance._get_owner_inventory()
		self.add_production(production_class(self.instance.get_component(StorageComponent).inventory, owner_inventory, production_line_id))


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
		self.instance._changed()

	def finish_production_now(self):
		"""Cheat, makes current production finish right now (and produce the resources).
		Useful to make trees fully grown at game start."""
		for production in self._productions.itervalues():
			production.finish_production_now()

	def has_production_line(self, prod_line_id):
		"""Checks if this instance has a production with a certain production line id"""
		return bool( self._get_production(prod_line_id) )

	def remove_production(self, production):
		"""Removes a production instance.
		@param production: Production instance"""
		production.remove() # production "destructor"
		if self.is_active(production):
			del self._productions[production.get_production_line_id()]
		else:
			del self._inactive_productions[production.get_production_line_id()]

	def remove_production_by_id(self, prod_line_id):
		"""
		Convenience method. Assumes, that this production line id has been added to this instance.
		@param prod_line_id: production line id to remove
		"""
		self.remove_production( self._get_production(prod_line_id) )

	def alter_production_time(self, modifier, prod_line_id=None):
		"""Multiplies the original production time of all production lines by modifier
		@param modifier: a numeric value
		@param prod_line_id: id of production line to alter. None means every production line"""
		if prod_line_id is None:
			for production in self.get_productions():
				production.alter_production_time(modifier)
		else:
			self._get_production(prod_line_id).alter_production_time(modifier)

	def remove(self):
		super(Producer, self).remove()
		for production in self.get_productions():
			self.remove_production(production)
		assert len(self.get_productions()) == 0 , 'Failed to remove %s ' % self.get_productions()


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

	def get_productions(self):
		"""Returns all productions, inactive and active ones, as list"""
		return self._productions.values() + self._inactive_productions.values()

	def get_production_lines(self):
		"""Returns all production lines that have been added.
		@return: a list of prodline ids"""
		return self._productions.keys() + self._inactive_productions.keys()

	def _get_production(self, prod_line_id):
		"""Returns a production of this producer by a production line id.
		@return: instance of Production or None"""
		if prod_line_id in self._productions:
			return self._productions[prod_line_id]
		elif prod_line_id in self._inactive_productions:
			return self._inactive_productions[prod_line_id]
		else:
			return None

	def is_active(self, production=None):
		"""Checks if a production, or the at least one production if production is None, is active"""
		if production is None:
			for production in self.get_productions():
				if not production.is_paused():
					return True
			return False
		else:
			assert production.get_production_line_id() in self._productions or \
			       production.get_production_line_id() in self._inactive_productions
			return not production.is_paused()

	def set_active(self, production=None, active=True):
		"""Pause or unpause a production (aka set it active/inactive).
		see also: is_active, toggle_active
		@param production: instance of Production. if None, we do it to all productions.
		@param active: whether to set it active or inactive"""
		if production is None:
			for production in self.get_productions():
				self.set_active(production, active)
			return

		line_id = production.get_production_line_id()
		if active:
			if not self.is_active(production):
				self.log.debug("ResHandler %s: reactivating production %s", self.instance.worldid, line_id)
				self._productions[line_id] = production
				del self._inactive_productions[line_id]
				production.pause(pause=False)
		else:
			if self.is_active(production):
				self.log.debug("ResHandler %s: deactivating production %s", self.instance.worldid, line_id)
				self._inactive_productions[line_id] = production
				del self._productions[line_id]
				production.pause()

		self.instance._changed()

	def toggle_active(self, production=None):
		if production is None:
			for production in self.get_productions():
				self.toggle_active(production)
		else:
			active = self.is_active(production)
			self.set_active(production, active = not active)
	def _on_production_change(self):
		"""Makes the instance act according to the producers
		current state"""
		state = self._get_current_state()
		if (state is PRODUCTION.STATES.waiting_for_res or\
			state is PRODUCTION.STATES.paused or\
			state is PRODUCTION.STATES.none):
			self.instance.act("idle", repeating=True)
		elif state is PRODUCTION.STATES.producing:
			self.instance.act("work", repeating=True)
		elif state is PRODUCTION.STATES.inventory_full:
			self.instance.act("idle_full", repeating=True)

	def get_status_icons(self):
		l = super(Producer, self).get_status_icons()
		if self.capacity_utilisation < ProductivityLowStatus.threshold:
			l.append( ProductivityLowStatus() )
		if not self.is_active():
			l.append( DecommissionedStatus() )
		return l


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
		for prod_line_id in self.production_queue:
			db("INSERT INTO production_queue (rowid, production_line_id) VALUES(?, ?)",
			   self.worldid, prod_line_id)

	def load(self, db, worldid):
		super(QueueProducer, self).load(db, worldid)
		self.__init()
		for (prod_line_id,) in db("SELECT production_line_id FROM production_queue WHERE rowid = ?", worldid):
			self.production_queue.append(prod_line_id)

	def add_production_by_id(self, production_line_id, production_class = Production):
		"""Convenience method.
		@param production_line_id: Production line from db
		@param production_class: Subclass of Production that does the production. If the object
		                         has a production_class-member, this will be used instead.
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
			prod = self.production_class(inventory=self.get_component(StorageComponent).inventory, owner_inventory=owner_inventory, prod_line_id=production_line_id)
			prod.add_production_finished_listener(self.on_queue_element_finished)
			self.add_production( prod )
		else:
			self.set_active(active=False)

	def cancel_all_productions(self):
		self.production_queue = []
		# Remove current productions, loose all progress and resources
		for production in self._productions.copy().itervalues():
			self.remove_production(production)
		for production in self._inactive_productions.copy().itervalues():
			self.remove_production(production)
		self.set_active(active=False)

