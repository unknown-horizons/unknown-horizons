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

from .default import DefaultPersonality


class OtherPersonality(DefaultPersonality):
	"""This personality makes the AI build larger settlements."""

	class LandManager(DefaultPersonality.LandManager):
		village_area_small = DefaultPersonality.LandManager.village_area_small * 2 # use this fraction of the area for the village if <= 1600 tiles are available for the settlement
		village_area_40 = DefaultPersonality.LandManager.village_area_40 * 2 # use this fraction of the area for the village if <= 2500 tiles are available for the settlement
		village_area_50 = DefaultPersonality.LandManager.village_area_50 * 2 # use this fraction of the area for the village if <= 3600 tiles are available for the settlement
		village_area_60 = DefaultPersonality.LandManager.village_area_60 * 2 # use this fraction of the area for the village if > 3600 tiles are available for the settlement
