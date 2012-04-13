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

from horizons.gui.tabs import  ProductionOverviewTab, InventoryTab
from horizons.constants import PRODUCTION
from horizons.world.component.storagecomponent import StorageComponent
from horizons.util.worldobject import WorldObject
from horizons.world.production.producer import Producer


class ResourceHandler(object):
	"""The ResourceHandler class acts as a basic class for describing objects
	that handle resources. This means the objects can provide resources for
	Collectors and have multiple productions. This is a base class, meaning
	you have to override a lot of functions in subclasses before you can actually
	use it. You can maybe understand our idea about the ResourceHandler if you
	look at the uml digramm: development/uml/production_classes.png

	A ResourceHandler must not have more than 1 production with the same prod line id.
	"""
	tabs = (ProductionOverviewTab, InventoryTab)

	## INIT/DESTRUCT
	def __init__(self, **kwargs):
		super(ResourceHandler, self).__init__(**kwargs)

	def __init(self):
		# list of collectors that are on the way here
		self.__incoming_collectors = []
		self.provided_resources = self._load_provided_resources()

	def initialize(self):
		super(ResourceHandler, self).initialize()
		self.__init()

	def save(self, db):
		super(ResourceHandler, self).save(db)

	def load(self, db, worldid):
		super(ResourceHandler, self).load(db, worldid)
		self.__init()

	def remove(self):
		super(ResourceHandler, self).remove()
		while self.__incoming_collectors: # safe list remove here
			self.__incoming_collectors[0].cancel()

	## INTERFACE
	def get_consumed_resources(self):
		"""Returns the needed resources that are used by the productions
		currently active."""
		needed_res = set()
		if self.has_component(Producer):
			prod_comp = self.get_component(Producer)
			for production in prod_comp._productions.itervalues():
				needed_res.update(production.get_consumed_resources().iterkeys())
		return list(needed_res)

	def get_produced_resources(self):
		"""Returns the resources, that are produced by productions, that are currently active"""
		produced_res = set()
		if self.has_component(Producer):
			prod_comp = self.get_component(Producer)
			for production in prod_comp._productions.itervalues():
				produced_res.update(production.get_produced_res().iterkeys())
		return list(produced_res)

	def get_stocked_provided_resources(self):
		"""Returns provided resources, where at least 1 ton is available"""
		return [res for res in self.provided_resources if self.get_component(StorageComponent).inventory[res] > 0]

	def get_currently_consumed_resources(self):
		"""Returns a list of resources, that are currently consumed in a production."""
		consumed_res = set()
		if self.has_component(Producer):
			prod_comp = self.get_component(Producer)
			for production in prod_comp._productions.itervalues():
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
						self.get_component(StorageComponent).inventory.get_free_space_for(res) > 0]

	def add_incoming_collector(self, collector):
		assert collector not in self.__incoming_collectors
		self.__incoming_collectors.append(collector)

	def remove_incoming_collector(self, collector):
		self.__incoming_collectors.remove(collector)

	def _get_owner_inventory(self):
		"""Returns the inventory of the owner to be able to retrieve special resources such as gold.
		The production system should be as decoupled as possible from actual world objects, so only use
		when there are no other possibilities"""
		try:
			return self.owner.get_component(StorageComponent).inventory
		except AttributeError: # no owner or no inventory, either way, we don't care
			return None

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
		remnant = self.get_component(StorageComponent).inventory.alter(res, -picked_up)
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
			amount = self.get_component(StorageComponent).inventory[res] - amount_from_collectors
			# the user can take away res, even if a collector registered for them
			# if this happens, a negative number would be returned. Use 0 instead.
			return max(amount, 0)

	## PROTECTED METHODS
	def _load_provided_resources(self):
		"""Returns a iterable obj containing all resources this building provides.
		This is outsourced from initiation to a method for the possiblity of overwriting it.
		Do not alter the returned list; if you need to do so, then copy it."""
		produced_res = set()
		for prod in self.get_component(Producer).get_productions():
			for res in prod.get_produced_res():
				produced_res.add(res)

		for res in self.additional_provided_resources:
			produced_res.add(res)

		return produced_res

	def transfer_to_storageholder(self, amount, res_id, transfer_to):
		"""Transfers amount of res_id to transfer_to.
		@param transfer_to: worldid or object reference
		@return: amount that was actually transfered (NOTE: this is different from the
						 return value of inventory.alter, since here are 2 storages involved)
		"""
		try:
			transfer_to = WorldObject.get_object_by_id( int(transfer_to) )
		except TypeError: # transfer_to not an int, assume already obj
			pass
		# take res from self
		ret = self.get_component(StorageComponent).inventory.alter(res_id, -amount)
		# check if we were able to get the planed amount
		ret = amount if amount < abs(ret) else abs(ret)
		# put res to transfer_to
		ret = transfer_to.get_component(StorageComponent).inventory.alter(res_id, amount-ret)
		self.get_component(StorageComponent).inventory.alter(res_id, ret) # return resources that did not fit
		return amount-ret

class StorageResourceHandler(ResourceHandler):
	"""Same as ResourceHandler, but for storage buildings such as warehouses.
	Provides all tradeable resources."""

	def get_consumed_resources(self):
		"""We collect everything we provide"""
		return self.provided_resources

	def _load_provided_resources(self):
		"""Storages provide every res.
		Do not alter the returned list; if you need to do so, then copy it."""
		return self.session.db.get_res(only_tradeable=True)

