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

from horizons.constants import RES
from horizons.util.python import decorators

class CompleteInventory(object):
	"""
	This class collects the information about all the resources of an ai player.
	"""

	def __init__(self, owner):
		self.owner = owner

	@property
	def money(self):
		return self.owner.inventory[RES.GOLD_ID]

	def move(self, ship, settlement, res, amount):
		"""
		Moves up to amount tons of res from the ship to the settlement
		"""
		if amount != 0:
			missing = ship.inventory.alter(res, -amount)
			overflow = settlement.inventory.alter(res, amount - missing)
			ship.inventory.alter(res, overflow)

	def unload_all(self, ship, settlement):
		items = [x for x in ship.inventory]
		for res, amount in items:
			self.move(ship, settlement, res, amount)

	def load_foundation_resources(self, ship, settlement):
		max_amounts = {RES.BOARDS_ID: 50, RES.FOOD_ID: 40, RES.TOOLS_ID: 30}
		for res, max_amount in max_amounts.iteritems():
			have = 0
			for ship_res, ship_amount in ship.inventory:
				if ship_res == res:
					have = ship_amount
					break
			self.move(ship, settlement, res, have - max_amount)

decorators.bind_all(CompleteInventory)
