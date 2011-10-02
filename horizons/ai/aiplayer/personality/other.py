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

from default import DefaultPersonality

class OtherPersonality(DefaultPersonality):
	""" this personality is just for testing """

	class SettlementFounder(DefaultPersonality.SettlementFounder):
		# found a settlement on a random island that is at least as large as the first element; if it is impossible then try the next size
		island_size_sequence = [1000, 300, 150]

	class AreaBuilder(DefaultPersonality.AreaBuilder):
		pass

	class ProductionBuilder(DefaultPersonality.ProductionBuilder, AreaBuilder):
		pass
