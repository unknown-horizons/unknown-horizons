import horizons.main

from horizons.world import storage
from horizons import constants
from horizons.world.component import Component
from horizons.world.storage import PositiveSizedSlotStorage, PositiveStorage, PositiveSizedSpecializedStorage, SettlementStorage, PositiveTotalNumSlotsStorage

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

	NAME = 'storagecomponent'

	storage_mapping = {
	    'PositiveStorage': PositiveStorage,
	    'PositiveSizedSlotStorage': PositiveSizedSlotStorage,
	    'PositiveTotalNumSlotStorage': PositiveTotalNumSlotsStorage,
	    'SlotsStorage': PositiveSizedSpecializedStorage,
	    'SettlementStorage': SettlementStorage # pseudo storage meaning to share settlement storage
	    }

	def __init__(self, inventory=None):
		super(StorageComponent, self).__init__()
		self.inventory = inventory

		# SettlementStorage is used as flag to signal using another inventory
		self.has_own_inventory = not isinstance(self.inventory, SettlementStorage)

	def initialize(self):
		# NOTE: also called on load (initialize usually isn't)
		if self.inventory is None:
			self.create_inventory()
		elif not self.has_own_inventory:
			self.inventory = self.instance.settlement.get_component(StorageComponent).inventory

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
			self.inventory.save(db, self.instance.worldid)

	def load(self, db, worldid):
		super(StorageComponent, self).load(db, worldid)
		self.initialize()
		if self.has_own_inventory:
			self.inventory.load(db, worldid)

	@classmethod
	def get_instance(cls, arguments=None):
		arguments = arguments or {}
		inventory = None
		if 'inventory' in arguments:
			assert len(arguments['inventory']) == 1, "You may not have more than one inventory!"
			key, value = arguments['inventory'].items()[0]
			storage = cls.storage_mapping[key]
			inventory = storage(**value)
		return cls(inventory=inventory)
