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

import collections
from typing import Any, Dict, Sequence, Union

import horizons.main
from horizons.component.componentholder import ComponentHolder
from horizons.component.storagecomponent import StorageComponent
from horizons.component.tradepostcomponent import TradePostComponent
from horizons.constants import PLAYER
from horizons.messaging import PlayerInventoryUpdated, PlayerLevelUpgrade, SettlerUpdate
from horizons.scenario import CONDITIONS
from horizons.scheduler import Scheduler
from horizons.util.color import Color
from horizons.util.difficultysettings import DifficultySettings
from horizons.util.inventorychecker import InventoryChecker
from horizons.util.python import decorators
from horizons.util.worldobject import WorldObject
from horizons.world.playerstats import PlayerStats


class Player(ComponentHolder, WorldObject):
	"""Class representing a player"""

	STATS_UPDATE_INTERVAL = 3 # seconds

	regular_player = True # either a human player or a normal AI player (not trader or pirate)
	component_templates = ({'StorageComponent': {'PositiveStorage': {}}},) # type: Sequence[Union[str, Dict[str, Any]]]

	def __init__(self, session, worldid, name, color, clientid=None, difficulty_level=None):
		"""
		@type session: horizons.session.Session
		@param session: Session instance
		@param worldid: player's worldid
		@param name: user-chosen name
		@param color: color of player (as Color)
		@param clientid: id of client
		@param inventory: {res: value} that are put in the players inventory
		"""
		assert isinstance(session, horizons.session.Session)
		self.session = session
		super().__init__(worldid=worldid)
		self.__init(name, color, clientid, difficulty_level, 0)

	def initialize(self, inventory):
		super().initialize()
		if inventory:
			for res, value in inventory.items():
				self.get_component(StorageComponent).inventory.alter(res, value)

	def __init(self, name, color, clientid, difficulty_level, max_tier_notification, settlerlevel=0):
		assert isinstance(color, Color)
		assert isinstance(name, str) and name
		try:
			self.name = str(name)
		except UnicodeDecodeError:
			# WORKAROUND: this line should be the only unicode conversion here.
			# however, if unicode() gets a parameter, it will fail if the string is already unicode.
			self.name = str(name, errors='ignore')
		self.color = color
		self.clientid = clientid
		self.difficulty = DifficultySettings.get_settings(difficulty_level)
		self.max_tier_notification = max_tier_notification
		self.settler_level = settlerlevel
		self._stats = None
		assert self.color.is_default_color, "Player color has to be a default color"

		if self.regular_player:
			SettlerUpdate.subscribe(self.notify_settler_reached_level)

	@property
	def is_local_player(self):
		return self is self.session.world.player

	def get_latest_stats(self):
		if self._stats is None or self._stats.collection_tick + PLAYER.STATS_UPDATE_FREQUENCY < Scheduler().cur_tick:
			self._stats = PlayerStats(self)
		return self._stats

	@property
	def settlements(self):
		"""Calculate settlements dynamically to save having a redundant list here"""
		return [settlement for settlement in self.session.world.settlements if
		        settlement.owner == self]

	def save(self, db):
		super().save(db)
		client_id = None
		if self.clientid is not None or self is self.session.world.player:
			client_id = self.clientid
		db("INSERT INTO player"
			" (rowid, name, color, client_id, settler_level,"
			" difficulty_level, max_tier_notification)"
			" VALUES(?, ?, ?, ?, ?, ?, ?)",
			self.worldid, self.name, self.color.id, client_id, self.settler_level,
			self.difficulty.level if self.difficulty is not None else None,
			self.max_tier_notification)

	@classmethod
	def load(cls, session, db, worldid):
		self = cls.__new__(cls)
		self.session = session
		self._load(db, worldid)
		return self

	def _load(self, db, worldid):
		"""This function makes it possible to load playerdata into an already allocated
		Player instance, which is used e.g. in Trader.load"""
		super().load(db, worldid)

		color, name, client_id, settlerlevel, difficulty_level, max_tier_notification = db(
			"SELECT color, name, client_id, settler_level, difficulty_level, max_tier_notification"
			" FROM player WHERE rowid = ?", worldid)[0]
		self.__init(name, Color.get(color), client_id, difficulty_level, max_tier_notification, settlerlevel=settlerlevel)

	def notify_settler_reached_level(self, message):
		"""Settler calls this to notify the player."""
		if message.sender.owner is not self:
			return
		if message.level > self.settler_level:
			self.settler_level = message.level
			self.session.scenario_eventhandler.check_events(CONDITIONS.settler_level_greater)
			for settlement in self.settlements:
				settlement.level_upgrade(self.settler_level)
			self._changed()
			PlayerLevelUpgrade.broadcast(self, self.settler_level, message.sender)

	def end(self):
		self._stats = None
		self.session = None

		if self.regular_player:
			SettlerUpdate.unsubscribe(self.notify_settler_reached_level)

	@decorators.temporary_cachedmethod(timeout=STATS_UPDATE_INTERVAL)
	def get_balance_estimation(self):
		"""This takes a while to calculate, so only do it every 2 seconds at most"""
		return sum(settlement.balance for settlement in self.settlements)

	@decorators.temporary_cachedmethod(timeout=STATS_UPDATE_INTERVAL)
	def get_statistics(self):
		"""Returns a namedtuple containing player-wide statistics"""
		Data = collections.namedtuple('Data', ['running_costs', 'taxes', 'sell_income', 'buy_expenses', 'balance'])
		# balance is duplicated here and above such that the version above
		# can be used independently and the one here is always perfectly in sync
		# with the other values here

		get_sum = lambda l, attr: sum(getattr(obj, attr) for obj in l)
		trade_posts = [s.get_component(TradePostComponent) for s in self.settlements]
		return Data(
		  running_costs=get_sum(self.settlements, 'cumulative_running_costs'),
		  taxes=get_sum(self.settlements, 'cumulative_taxes'),
		  sell_income=get_sum(trade_posts, 'sell_income'),
		  buy_expenses=get_sum(trade_posts, 'buy_expenses'),
		  balance=get_sum(self.settlements, 'balance'),
		)


class HumanPlayer(Player):
	"""Class for players that physically sit in front of the machine where the game is run"""

	def __init(self, *args, **kwargs):
		super().__init(*args, **kwargs)
		self.__inventory_checker = InventoryChecker(PlayerInventoryUpdated, self.get_component(StorageComponent), 4)

	def end(self):
		if hasattr(self, '__inventory_checker'):
			self.__inventory_checker.remove()
		super().end()
