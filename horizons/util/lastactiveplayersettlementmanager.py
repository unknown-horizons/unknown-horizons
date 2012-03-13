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

import weakref

from horizons.util.python import ManualConstructionSingleton
from horizons.util import Point
from horizons.util.messaging.message import LastSettlementChanged

class LastActivePlayerSettlementManager(object):
	"""Keeps track of the last active (hovered over) player's settlement.
	Provides it as global reference, but stores as weak reference as not to disturb anything.

	Provide new mouse info to it via update().
	Retrieve settlement via get().
	Hooks itself to view automatically.
	"""
	__metaclass__ = ManualConstructionSingleton

	def __init__(self, session):
		self._settlement = None
		self.session = session
		self.session.view.add_change_listener(self._on_scroll)

	def remove(self):
		self._settlement = None
		self.session.view.remove_change_listener(self._on_scroll)

	def update(self, current):
		"""Update to new world position. Sets internal state to new settlement or no settlement"""
		settlement = self.session.world.get_settlement(Point(int(round(current.x)), int(round(current.y))))

		new_settlement = weakref.ref(settlement) if \
		  settlement and settlement.owner.is_local_player else None

		if self.get() is not (new_settlement() if new_settlement else new_settlement):
			self._settlement = new_settlement
			self.session.message_bus.broadcast(LastSettlementChanged(self))


			# set cityinfo for any settlement
			self.session.ingame_gui.cityinfo_set(settlement)

			# set res info only if it's a player settlement
			self.session.ingame_gui.resource_overview.set_inventory_instance(settlement)

	def get(self):
		"""The last settlement belonging to the player the mouse has hovered above"""
		ref = self._settlement
		if ref is not None: # weakref
			return ref()
		else:
			return None

	def _on_scroll(self):
		"""Called when view changes"""
		if not hasattr(self.session, "cursor"): # not inited yet
			return
		pos = self.session.cursor.__class__.last_event_pos
		if pos is not None:
			loc = self.session.cursor.get_exact_world_location_from_event( pos )
			self.update(loc)

