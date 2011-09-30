import horizons.main

from horizons.world import storage
from horizons import constants
from horizons.util import worldobject
from horizons.world.component import Component
from horizons.constants import STORAGE

class StorageComponent(Component):
	"""The StorageComponent class is used as as a parent class for everything that
	has an inventory. Examples for these classes are ships, settlements,
	buildings, etc. Basically it just adds an inventory, nothing more, nothing
	less.
	If you want something different than a PositiveSizedSlotStorage, you'll have to
	overwrite that in the subclass.

	TUTORIAL:
	Continue to horizons/world/provider.py for further digging.
	"""

	NAME='storagecomponent'

	has_own_inventory = True # some objs share inventory, which requires different handling here.

	def __init__(self, instance):
		super(StorageComponent, self).__init__(instance)
		self.__init()

	def __init(self):
		self.create_inventory()
		if self.has_own_inventory:
			self.inventory.add_change_listener(self.instance._changed)

	def remove(self):
		super(StorageComponent, self).remove()
		if self.has_own_inventory:
			# no changelister calls on remove
			self.inventory.clear_change_listeners()
			# remove inventory to prevent any action here in subclass remove
			self.inventory.reset_all()

	def create_inventory(self):
		"""Some buildings don't have an own inventory (e.g. storage building). Those can just
		overwrite this function to do nothing. see also: save_inventory() and load_inventory()"""
		db_data = horizons.main.db.cached_query("SELECT resource, size FROM storage WHERE object_id = ?", \
		                           self.instance.id)

		if len(db_data) == 0:
			# no db data about inventory. Create default inventory.
			self.inventory = storage.PositiveSizedSlotStorage(constants.STORAGE.DEFAULT_STORAGE_SIZE)
		else:
			# specialised storage; each res and limit is stored in db.
			self.inventory = storage.PositiveSizedSpecializedStorage()
			for res, size in db_data:
				self.inventory.add_resource_slot(res, size)

	def save(self, db):
		super(StorageComponent, self).save(db)
		if self.has_own_inventory:
			self.inventory.save(db, self.worldid)

	def load(self, db, worldid):
		super(StorageComponent, self).load(db, worldid)
		self.__init()
		if self.has_own_inventory:
			self.inventory.load(db, worldid)


class PositiveStorageComponent(StorageComponent):
	"""StorageComponent that is to be used if a PositiveStorage is wanted"""

	def create_inventory(self):
		self.inventory = storage.PositiveStorage()

class PositiveSizedSlotStorageComponent(StorageComponent):
	"""StorageComponent that is to be used if a PositiveSizedSlots wanted"""

	def create_inventory(self):
		self.inventory = storage.PositiveSizedSlotStorage(0)

class ShipStorageComponent(StorageComponent):
	"""StorageComponent that is to be used for ships"""
	def create_inventory(self):
		self.inventory = storage.PositiveTotalNumSlotsStorage(STORAGE.SHIP_TOTAL_STORAGE, STORAGE.SHIP_TOTAL_SLOTS_NUMBER)
