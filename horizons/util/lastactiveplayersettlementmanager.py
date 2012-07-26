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
from horizons.util import Point, WorldObject
from horizons.messaging import NewPlayerSettlementHovered, HoverSettlementChanged, NewSettlement

def resolve_weakref(ref):
	"""Resolves a weakref to a hardref, where the ref itself can be None"""
	if ref is None:
		return None
	else:
		return ref()

def create_weakref(obj):
	"""Safe create weakref, that supports None"""
	if obj is None:
		return None
	else:
		return weakref.ref(obj)

class LastActivePlayerSettlementManager(object):
	"""Keeps track of the last active (hovered over) player's settlement.
	Provides it as global reference, but stores as weak reference as not to disturb anything.

	Provide new mouse info to it via update().
	Retrieve settlement via get().
	Hooks itself to view automatically.
	"""
	__metaclass__ = ManualConstructionSingleton

	def __init__(self, session):
		self.session = session
		self.session.view.add_change_listener(self._on_scroll)

		# settlement mouse currently is above or None
		self._cur_settlement = None

		# last settlement of player mouse was on, only None at startup
		self._last_player_settlement = None

		# whether last known event was not on a player settlement
		# can be used to detect reentering the area of _last_player_settlement
		self._last_player_settlement_hovered_was_none = True

		NewSettlement.subscribe(self._on_new_settlement_created)

	def save(self, db):
		if self._last_player_settlement is not None:
			db("INSERT INTO last_active_settlement(type, value) VALUES(?, ?)", "PLAYER", self._last_player_settlement().worldid)
		if self._cur_settlement is not None:
			db("INSERT INTO last_active_settlement(type, value) VALUES(?, ?)", "ANY", self._cur_settlement().worldid)

		db("INSERT INTO last_active_settlement(type, value) VALUES(?, ?)", "LAST_NONE_FLAG", self._last_player_settlement_hovered_was_none)

	def load(self, db):
		data = db('SELECT value FROM last_active_settlement WHERE type = "PLAYER"')
		self._last_player_settlement = weakref.ref(WorldObject.get_object_by_id(data[0][0])) if data else None
		data = db('SELECT value FROM last_active_settlement WHERE type = "ANY"')
		self._cur_settlement = weakref.ref(WorldObject.get_object_by_id(data[0][0])) if data else None
		data = db('SELECT value FROM last_active_settlement WHERE type = "LAST_NONE_FLAG"')
		self._last_player_settlement_hovered_was_none = bool(data[0][0])

	def remove(self):
		self._last_player_settlement = None
		self._cur_settlement = None
		self.session.view.remove_change_listener(self._on_scroll)

	def update(self, current):
		"""Update to new world position. Sets internal state to new settlement or no settlement
		@param current: some kind of position coords with x- and y-values"""
		settlement = self.session.world.get_settlement(Point(int(round(current.x)), int(round(current.y))))

		# check if it's a new settlement independent of player
		if resolve_weakref(self._cur_settlement) is not settlement:
			self._cur_settlement = create_weakref(settlement)
			HoverSettlementChanged.broadcast(self, settlement)

		# player-sensitive code
		new_player_settlement = weakref.ref(settlement) if \
		  settlement and settlement.owner.is_local_player else None

		need_msg = False
		# check if actual last player settlement is a new one
		if new_player_settlement is not None and \
		   resolve_weakref(self._last_player_settlement) is not resolve_weakref( new_player_settlement):
			self._last_player_settlement = new_player_settlement
			need_msg = True

		# check if we changed to or from None
		# this doesn't change the last settlement, but we need a message
		if (new_player_settlement is None and not self._last_player_settlement_hovered_was_none) or \
		   (new_player_settlement is not None and self._last_player_settlement_hovered_was_none):
			need_msg = True

		if need_msg:
			NewPlayerSettlementHovered.broadcast(self, resolve_weakref(new_player_settlement))
		self._last_player_settlement_hovered_was_none = (new_player_settlement is None)

	def get(self, get_current_pos=False):
		"""The last settlement belonging to the player the mouse has hovered above.
		@param get_current_pos: get current position even if it's None
		"""
		if get_current_pos and self._last_player_settlement_hovered_was_none:
			return None
		return resolve_weakref(self._last_player_settlement)

	def get_current_settlement(self):
		"""Returns settlement mouse currently hovers over or None"""
		return resolve_weakref(self._cur_settlement)

	def _on_scroll(self):
		"""Called when view changes. Scrolling and zooming can change cursor position."""
		if not hasattr(self.session, "cursor"): # not inited yet
			return
		pos = self.session.cursor.__class__.last_event_pos
		if pos is not None:
			loc = self.session.cursor.get_exact_world_location( pos )
			self.update(loc)

	def _on_new_settlement_created(self, msg):
		# if the player has created a new settlement, it is the current one, even
		# if the mouse hasn't hovered over it. Required when immediately entering build menu.
		if msg.settlement.owner.is_local_player:
			self._last_player_settlement = weakref.ref(msg.settlement)
			self._last_player_settlement_hovered_was_none = False
