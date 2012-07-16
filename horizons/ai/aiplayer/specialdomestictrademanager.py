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

import logging

from collections import defaultdict

from mission.specialdomestictrade import SpecialDomesticTrade
from horizons.util.python import decorators
from horizons.component.storagecomponent import StorageComponent

class SpecialDomesticTradeManager(object):
	"""
	An object of this class manages the special domestic trade routes of one AI player.

	These are called the special routes because they transport existing resources while
	the regular routes transport resources that have been produced for other settlements.

	The current implementation is limited to one active route between each (directed)
	pair of settlements. The routes are automatically removed when they have
	been used once or when the ship gets destroyed.
	"""

	log = logging.getLogger("ai.aiplayer.specialdomestictrade")

	def __init__(self, owner):
		super(SpecialDomesticTradeManager, self).__init__()
		self.owner = owner
		self.world = owner.world
		self.session = owner.session

	def _trade_mission_exists(self, source_settlement_manager, destination_settlement_manager):
		for mission in self.owner.missions:
			if not isinstance(mission, SpecialDomesticTrade):
				continue
			if mission.source_settlement_manager is source_settlement_manager and mission.destination_settlement_manager is destination_settlement_manager:
				return True
		return False

	def _add_route(self):
		"""
		Add a new special domestic trade route if possible.

		The route is created between the two settlements that need resources with most
		value transported between them but the actual mission will be unaware of the
		initial reasons for creating it and pick up whatever resources need to be
		transported when it gets to the source warehouse.
		"""

		ship = None
		for possible_ship, state in self.owner.ships.iteritems():
			if state is self.owner.shipStates.idle:
				ship = possible_ship
				break
		if not ship:
			#self.log.info('%s no available ships', self)
			return

		options = defaultdict(lambda: [])
		# try to set up a new route where the first settlement gets an extra shipment of a resource from the second settlement
		for source_settlement_manager in self.owner.settlement_managers:
			for destination_settlement_manager in self.owner.settlement_managers:
				if destination_settlement_manager is source_settlement_manager or self._trade_mission_exists(source_settlement_manager, destination_settlement_manager):
					continue

				source_resource_manager = source_settlement_manager.resource_manager
				source_inventory = source_settlement_manager.settlement.get_component(StorageComponent).inventory
				destination_resource_manager = destination_settlement_manager.resource_manager
				destination_inventory = destination_settlement_manager.settlement.get_component(StorageComponent).inventory

				for resource_id, limit in destination_resource_manager.resource_requirements.iteritems():
					if destination_inventory[resource_id] >= limit:
						continue # the destination settlement doesn't need the resource
					if source_inventory[resource_id] <= source_resource_manager.resource_requirements[resource_id]:
						continue # the source settlement doesn't have a surplus of the resource

					price = self.session.db.get_res_value(resource_id)
					tradable_amount = min(ship.get_component(StorageComponent).inventory.get_limit(resource_id), limit - destination_inventory[resource_id],
						source_inventory[resource_id] - source_resource_manager.resource_requirements[resource_id])
					options[(source_settlement_manager, destination_settlement_manager)].append((tradable_amount * price, tradable_amount, price, resource_id))

		if not options:
			#self.log.info('%s no interesting options', self)
			return

		final_options = []
		for (source_settlement_manager, destination_settlement_manager), option in sorted(options.iteritems()):
			total_amount = 0
			total_value = 0
			for _, amount, price, resource_id in option:
				amount = min(amount, ship.get_component(StorageComponent).inventory.get_limit(resource_id) - total_amount)
				total_value += amount * price
				total_amount += amount
			final_options.append((total_value, source_settlement_manager, destination_settlement_manager))

		source_settlement_manager, destination_settlement_manager = max(final_options)[1:]
		self.owner.start_mission(SpecialDomesticTrade(source_settlement_manager, destination_settlement_manager, ship, self.owner.report_success, self.owner.report_failure))

	def tick(self):
		self._add_route()

	def __str__(self):
		return '%s.SpecialDomesticTradeManager' % self.owner

decorators.bind_all(SpecialDomesticTradeManager)
