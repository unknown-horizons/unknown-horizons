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
from storageholder import StorageHolder
from horizons.world.production.production import Production
from horizons.gui.tabs import TabWidget, ProductionOverviewTab, InventoryTab


class ResourceHandler(StorageHolder):

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
		self.provided_resources = [] # Stores a list of resource ids this resourcehandler provides for pickup
		for res in horizons.main.db("SELECT resource FROM production WHERE amount > 0 AND \
																production_line IN \
																(SELECT id FROM production_line WHERE object_id = ? )", self.id):
			self.provided_resources.append(res[0])
		# list of collectors that are on the way here
		self.__incoming_collectors = WeakList()

	def remove(self):
		super(ResourceHandler, self).remove()

	def save(self, db):
		super(ResourceHandler, self).save(db)
		for production in self._productions.itervalues():
			production.save(db)
			# set us to owner of that production
			db("UPDATE production SET owner = ? WHERE rowid = ?", self.getId(), production.getId())

	def load(self, db, worldid):
		super(ResourceHandler, self).load(db, worldid)
		self.__init()
		# load all productions
		for production in db('SELECT rowid FROM production WHERE owner = ?', worldid):
			self.log.debug('loading production %s at %s', production[0], self.getId())
			self.add_production( self.load_production(db, production[0]) )

	## INTERFACE
	def get_consumed_resources(self):
		"""Returns the needed resources that are used by the productions
		currently active."""
		needed_res = set()
		# Now get needed res for each production and add them
		for production in self._productions.itervalues():
			needed_res.update(production.get_consumed_resources().iterkeys())
		return list(needed_res)

	def get_provided_resources(self):
		"""Returns the provided resources by this building."""
		return self.provided_resources

	def get_stocked_provided_resources(self):
		"""Returns provided resources, where at least 1 ton is available"""
		return [res for res in self.get_provided_resources() if self.inventory[res] > 0]

	def get_needed_resources(self):
		"""Returns list of resources, where free space in the inventory exists."""
		return [res for res in self.get_consumed_resources() if \
						self.inventory.get_space_for_res(res) > 0]

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
		raise NotImplementedError, "This function has to be overidden!"

	def load_production(self, db, production_id):
		"""Load a saved production and return it. Needs to be implemented when add_production is.
		@return Production instance"""
		raise NotImplementedError, "This function has to be overidden!"

	def remove_production(self, production):
		"""@param production: Production instance"""
		if self.is_active(production):
			del self._productions[production.get_production_line_id()]
		else:
			del self._inactive_productions[production.get_production_line_id()]

	def pickup_resources(self, res, amount, collector):
		"""Try to get amount number of resources of id res_id that are in stock
		and removes them from the stock. Will return smaller amount if not
		enough resources are available.
		@param res: int ressouce id
		@param amount: int amount that is to be picked up
		@param collector: the collector instance, that picks it up
		@return: int number of resources that can actually be picked up"""
		picked_up = self.get_available_pickup_amount(res, collector)
		if picked_up > amount:
			picked_up = amount
		remnant = self.inventory.alter(res, -picked_up)
		assert remnant == 0
		return picked_up

	def get_available_pickup_amount(self, res, collector):
		"""Returns how much of res a collector may pick up. It's the stored amount minus the amount
		that other collectors are getting"""
		return self.inventory[res] - \
					 sum([c.job.amount for c in self.__incoming_collectors if \
								c != collector and c.job.res == res])

	def set_active(self, production=None, active=True):
		"""Pause or unpause a production (aka set it active/inactive).
		see also: is_active, toggle_active
		@param production: instance of Production. if None, we do it to all productions.
		@param active: wether to set it active or inactive"""
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

	def is_active(self, production):
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

	def show_menu(self):
		horizons.main.session.ingame_gui.show_menu(TabWidget(tabs= [ProductionOverviewTab(self), InventoryTab(self)]))

	## PROTECTED METHODS
	def _get_productions(self):
		"""Returns all productions, inactive and active ones, as list"""
		tmp = self._productions.values()
		tmp.extend(self._inactive_productions.values())
		return tmp



class StorageResourceHandler(ResourceHandler):
	"""Same as ResourceHandler, but for storage buildings such as branch offices.
	Proides all tradeable resources."""
	def __init__(self, **kwargs):
		super(StorageResourceHandler, self).__init__( **kwargs)
		self.__init()

	def __init(self):
		# we provide every tradeable res here.
		self.provided_resources = []
		for res in horizons.main.db("SELECT id FROM resource WHERE tradeable = 1"):
			self.provided_resources.append(res[0])

	def load(self, db, worldid):
		super(StorageResourceHandler, self).load(db, worldid)
		self.__init()

	def get_consumed_resources(self):
		"""We collect everything we also provide"""
		return self.provided_resources
