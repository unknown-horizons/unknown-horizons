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
import horizons.main

from horizons.util import WeakList
from horizons.world.storageholder import StorageHolder
from horizons.gui.tabs import  ProductionOverviewTab, InventoryTab
from horizons.world.production.production import Production
from horizons.constants import PRODUCTION


class ResourceHandler(StorageHolder):
	"""The ResourceHandler class acts as a basic class for describing objects
	that handle resources. This means the objects can provide resources for 
	Collectors and have multiple productions. This is a base class, meaning 
	you have to override a lot of functions in subclasses before you can actually
	use it. You can maybe understand our idea about the ResourceHandler if you 
	look at the uml digramm: development/uml/production_classes.png
	TUTORIAL:
	You should now look at some of the implementations of the ResourceHandler.
	You will find some in world/production/producer.py
	"""
	tabs = (ProductionOverviewTab, InventoryTab)

	## INIT/DESTRUCT
	def __init__(self, **kwargs):
		super(ResourceHandler, self).__init__(**kwargs)
		self.__init()

	def __init(self):
		# we store productions in 2 dicts, one for the active ones, and one for the inactive ones.
		# the inactive ones won't get considered for needed_resources and such.
		# the production_line id is the key in the dict (=> a building must not have two identical
		# production lines)
		self._productions = {}
		self._inactive_productions = {}
		# Stores a set of resource ids this resourcehandler provides for pickup
		self.provided_resources = self._load_provided_resources()

		# list of collectors that are on the way here
		self.__incoming_collectors = []

	def save(self, db):
		super(ResourceHandler, self).save(db)
		for production in self._get_productions():
			production.save(db)
			# set us to owner of that production
			db("UPDATE production SET owner = ? WHERE rowid = ?", self.getId(), production.getId())

	def load(self, db, worldid):
		super(ResourceHandler, self).load(db, worldid)
		self.__init()
		# load all productions
		for production in db('SELECT rowid FROM production WHERE owner = ?', worldid):
			self.add_production( self.load_production(db, production[0]) )

	def remove(self):
		super(ResourceHandler, self).remove()
		for production in self._get_productions():
			self.remove_production(production)
		assert len(self._get_productions()) == 0 , 'Failed to remove %s ' % self._get_productions()
		while self.__incoming_collectors: # safe list remove here
			self.__incoming_collectors[0].cancel()

	## INTERFACE
	def get_consumed_resources(self):
		"""Returns the needed resources that are used by the productions
		currently active."""
		needed_res = set()
		for production in self._productions.itervalues():
			needed_res.update(production.get_consumed_resources().iterkeys())
		return list(needed_res)

	def get_stocked_provided_resources(self):
		"""Returns provided resources, where at least 1 ton is available"""
		return [res for res in self.provided_resources if self.inventory[res] > 0]

	def get_currently_consumed_resources(self):
		"""Returns a list of resources, that are currently consumed in a production."""
		consumed_res = set()
		for production in self._productions.itervalues():
			if production.get_state() == PRODUCTION.STATES.producing:
				consumed_res.update(production.get_consumed_resources().iterkeys())
		return list(consumed_res)

	def get_currently_not_consumed_resources(self):
		"""Needed, but not currenlty consumed resources.
		Opposite of get_currently_consumed_resources."""
		# use set types since they support the proper operation
		currently_consumed = frozenset(self.get_currently_consumed_resources())
		consumed = frozenset(self.get_consumed_resources())
		return list( consumed - currently_consumed )

	def get_needed_resources(self):
		"""Returns list of resources, where free space in the inventory exists."""
		return [res for res in self.get_consumed_resources() if \
						self.inventory.get_free_space_for(res) > 0]

	def add_incoming_collector(self, collector):
		assert collector not in self.__incoming_collectors
		self.__incoming_collectors.append(collector)

	def remove_incoming_collector(self, collector):
		self.__incoming_collectors.remove(collector)

	def add_production(self, production):
		"""Override this function by the object using it.
		Should add the provided production to the self._productions dict.
		@param production: Production instance
		"""
		raise NotImplementedError, "This function has to be overridden!"

	def add_production_by_id(self, production_line_id, production_class = Production):
		"""Convenience method.
		@param production_line_id: Production line from db
		@param production_class: Subclass of Production that does the production. If the object
		                         has a production_class-member, this will be used instead.
		"""
		if hasattr(self, "production_class"):
			production_class = self.production_class
		self.add_production(production_class(self.inventory, production_line_id))

	def load_production(self, db, production_id):
		"""Load a saved production and return it. Needs to be implemented when add_production is.
		@return Production instance"""
		raise NotImplementedError, "This function has to be overridden!"

	def remove_production(self, production):
		"""@param production: Production instance"""
		production.remove() # production "destructor"
		if self.is_active(production):
			del self._productions[production.get_production_line_id()]
		else:
			del self._inactive_productions[production.get_production_line_id()]

	def remove_production_by_id(self, ident):
		"""
		@param ident: production line id
		"""
		to_remove = [] # save production to remove here for safe removal
		for production in self._get_productions():
			if production.get_production_line_id() == ident:
				to_remove.append(production)
		if len(to_remove) == 0:
			raise ValueError, "Production %s doesn't have a production line %s" % (self, ident)
		for production in to_remove: # we can safely iterate, to_remove isn't changed
			self.remove_production(production)

	def has_production_line(self, id):
		"""Checks for a production line id"""
		return bool( [ p for p in self._get_productions() if p.get_production_line_id() == id ] )

	def get_production_progress(self):
		"""Can be used to return the overall production process."""
		raise NotImplementedError, "This function has to be overridden!"

	def get_production_lines(self):
		"""Returns all production lines that have been added.
		@return: a list of prodline ids"""
		return [ production.get_production_line_id() for production in self._get_productions() ]

	def pickup_resources(self, res, amount, collector):
		"""Try to get amount number of resources of id res_id that are in stock
		and removes them from the stock. Will return smaller amount if not
		enough resources are available.
		@param res: int resource id
		@param amount: int amount that is to be picked up
		@param collector: the collector instance, that picks it up
		@return: int number of resources that can actually be picked up"""
		picked_up = self.get_available_pickup_amount(res, collector)
		assert picked_up >= 0
		if picked_up > amount:
			picked_up = amount
		remnant = self.inventory.alter(res, -picked_up)
		assert remnant == 0
		return picked_up

	def get_available_pickup_amount(self, res, collector):
		"""Returns how much of res a collector may pick up. It's the stored amount minus the amount
		that other collectors are getting"""
		if not res in self.provided_resources:
			return 0 # we don't provide this, and give nothing away because we need it ourselves.
		else:
			amount_from_collectors = sum([c.job.amount for c in self.__incoming_collectors if \
			                              c != collector and c.job.res == res])
			amount = self.inventory[res] - amount_from_collectors
			# the user can take away res, even if a collector registered for them
			# if this happens, a negative number would be returned. Use 0 instead.
			return max(amount, 0)

	def alter_production_time(self, modifier):
		"""Multiplies the original production time of all production lines by modifier
		@param modifier: a numeric value"""
		for production in self._get_productions():
			production.alter_production_time(modifier)

	def set_active(self, production=None, active=True):
		"""Pause or unpause a production (aka set it active/inactive).
		see also: is_active, toggle_active
		@param production: instance of Production. if None, we do it to all productions.
		@param active: whether to set it active or inactive"""
		if production is None:
			for production in self._get_productions():
				self.set_active(production, active)
			return

		line_id = production.get_production_line_id()
		if active:
			assert not self.is_active(production)
			self.log.debug("ResHandler %s: reactivating production %s", self.getId(), line_id)
			production.pause(pause=False)
			self._productions[line_id] = production
			del self._inactive_productions[line_id]
		else:
			assert self.is_active(production)
			self.log.debug("ResHandler %s: deactivating production %s", self.getId(), line_id)
			production.pause()
			self._inactive_productions[line_id] = production
			del self._productions[line_id]

		self._changed()

	def is_active(self, production=None):
		"""Checks if a production, or the at least one production if production is None, is active"""
		if production is None:
			for production in self._get_productions():
				if not production.is_paused():
					return True
			return False
		else:
			assert production.get_production_line_id() in self._productions or \
			       production.get_production_line_id() in self._inactive_productions
			return not production.is_paused()

	def toggle_active(self, production=None):
		if production is None:
			for production in self._get_productions():
				self.toggle_active(production)
			return

		active = self.is_active(production)
		self.set_active(production, active = not active)

	## PROTECTED METHODS
	def _get_productions(self):
		"""Returns all productions, inactive and active ones, as list"""
		return self._productions.values() + self._inactive_productions.values()

	def _load_provided_resources(self):
		provided_res = set()
		for res in horizons.main.db("SELECT resource FROM balance.production WHERE amount > 0 AND \
		production_line IN (SELECT id FROM production_line WHERE object_id = ? )", self.id):
			provided_res.add(res[0])
		return provided_res

class StorageResourceHandler(ResourceHandler):
	"""Same as ResourceHandler, but for storage buildings such as branch offices.
	Provides all tradeable resources."""

	def get_consumed_resources(self):
		"""We collect everything we provide"""
		return self.provided_resources

	def _load_provided_resources(self):
		# we provide every tradeable res here.
		provided_resources = []
		for res in horizons.main.db("SELECT id FROM resource WHERE tradeable = 1"):
			provided_resources.append(res[0])
		return provided_resources
