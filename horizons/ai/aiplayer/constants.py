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

class BUILD_RESULT:
	OK = 0
	NEED_RESOURCES = 1
	IMPOSSIBLE = 2
	UNKNOWN_ERROR = 3

class PRODUCTION_PURPOSE:
	NONE = 1
	RESERVED = 2
	BRANCH_OFFICE = 3
	ROAD = 4
	FISHER = 5
	LUMBERJACK = 6
	TREE = 7
	STORAGE = 8
	FARM = 9
	UNUSED_POTATO_FIELD = 10
	POTATO_FIELD = 11
	CLAY_PIT = 12
	BRICKYARD = 13
	UNUSED_PASTURE = 14
	PASTURE = 15
	WEAVER = 16
	UNUSED_SUGARCANE_FIELD = 17
	SUGARCANE_FIELD = 18
	DISTILLERY = 19

	@classmethod
	def get_used_purpose(cls, purpose):
		if purpose == cls.UNUSED_POTATO_FIELD:
			return cls.POTATO_FIELD
		elif purpose == cls.UNUSED_PASTURE:
			return cls.PASTURE
		elif purpose == cls.UNUSED_SUGARCANE_FIELD:
			return cls.SUGARCANE_FIELD
		return None

	@classmethod
	def get_unused_purpose(cls, purpose):
		if purpose == cls.POTATO_FIELD:
			return cls.UNUSED_POTATO_FIELD
		elif purpose == cls.PASTURE:
			return cls.UNUSED_PASTURE
		elif purpose == cls.SUGARCANE_FIELD:
			return cls.UNUSED_SUGARCANE_FIELD
		return None
