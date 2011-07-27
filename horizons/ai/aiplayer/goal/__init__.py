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

import logging

from horizons.util import WorldObject
from horizons.util.python import decorators

class Goal(WorldObject):
	"""
	An object of this class describes a goal that an AI player attempts to fulfil.
	"""

	log = logging.getLogger("ai.aiplayer.goal")

	def __init__(self, owner):
		super(Goal, self).__init__()
		self.__init(owner)

	def __init(self, owner):
		self.owner = owner

	def save(self, db):
		pass

	def load(self, db, worldid, owner):
		super(Goal, self).load(db, worldid)
		self.__init(owner)

	@property
	def priority(self):
		return 0

	@property
	def active(self):
		return False

	@property
	def can_be_activated(self):
		return True

	def execute(self):
		raise NotImplementedError, "This function has to be overridden."

	def update(self):
		pass

	def __lt__(self, other):
		if self.priority != other.priority:
			return self.priority < other.priority
		return self.worldid < other.worldid

decorators.bind_all(Goal)
