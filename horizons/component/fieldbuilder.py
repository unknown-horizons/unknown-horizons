# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from horizons.command.building import Build
from horizons.component import Component
from horizons.entities import Entities


class FieldBuilder(Component):
	"""
	Component for production buildings. It adds a hook `fill_range` to fill the
	building range with a specified 1x1 field. The usual buildability constraints
	for that field apply. `fill_range` will only succeed if the cost for filling
	the entire range can be paid - there is no automated partial construction.
	For GUI purposes, some more information is exposed:
	- how many fields would be built at once
	- total resource cost
	- whether the build is affordable right now.
	"""
	NAME = 'FieldBuilder'

	def __init__(self, field):
		super().__init__()
		self.field = Entities.buildings[field]

	@property
	def how_many(self):
		return len(list(self.coords_in_range()))

	@property
	def total_cost(self):
		return {res: amount * self.how_many for res, amount in self.field.costs.items()}

	def check_resources(self):
		return Build.check_resources({}, self.total_cost, self.instance.owner,
		                             [self.instance.settlement])

	def coords_in_range(self):
		where = self.instance.position.get_radius_coordinates(self.instance.radius)
		for coords in where:
			tile = self.instance.island.get_tile_tuple(coords)
			if tile is None or tile.object is not None:
				continue
			if not self.field.check_build(self.instance.session, tile):
				continue
			yield coords

	def fill_range(self):
		for (x, y) in self.coords_in_range():
			cmd = Build(self.field, x, y, self.instance.island)
			cmd.execute(self.instance.session)
