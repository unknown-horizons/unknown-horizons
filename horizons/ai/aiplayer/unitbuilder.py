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

from horizons.util.python import decorators
from horizons.constants import BUILDINGS, PRODUCTIONLINES
from horizons.command.production import AddProduction
from horizons.world.production.producer import Producer

class UnitBuilder(object):
	"""An object of this class builds the units of one player."""

	log = logging.getLogger("ai.aiplayer.unit_builder")

	def __init__(self, owner):
		super(UnitBuilder, self).__init__()
		self.owner = owner

	def _get_boat_builders(self):
		"""Return a list of all boat builders owned by the player."""
		result = [] # [building, ...]
		for settlement_manager in self.owner.settlement_managers:
			result.extend(settlement_manager.settlement.buildings_by_id.get(BUILDINGS.BOATBUILDER_CLASS, []))
		return result

	def build_ship(self):
		"""Build a new usable fishing boat."""
		boat_builder = self._get_boat_builders()[0]
		AddProduction(boat_builder.get_component(Producer), PRODUCTIONLINES.HUKER).execute(self.owner.session)
		production = boat_builder.get_component(Producer)._get_production(PRODUCTIONLINES.HUKER)
		production.add_production_finished_listener(self._ship_built)
		self.log.info('%s started building a ship', self)

	def _ship_built(self, production):
		"""Called when a new ship has been built."""
		self.log.info('%s ship building finished', self)
		self.owner.refresh_ships()

	@property
	def num_ships_being_built(self):
		"""Return the number of ships being built by all the boat builders of the player."""
		return sum(len(boat_builder.get_component(Producer).get_production_lines()) for boat_builder in self._get_boat_builders())

	def __str__(self):
		return '%s UnitBuilder' % self.owner

decorators.bind_all(UnitBuilder)
