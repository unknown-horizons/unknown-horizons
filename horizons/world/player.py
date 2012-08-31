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

import collections

import horizons.main

from horizons.constants import PLAYER
from horizons.world.playerstats import PlayerStats
from horizons.util import WorldObject, Callback, Color, DifficultySettings, decorators
from horizons.scenario import CONDITIONS
from horizons.scheduler import Scheduler
from horizons.component.componentholder import ComponentHolder
from horizons.component.storagecomponent import StorageComponent
from horizons.messaging import SettlerUpdate, NewDisaster
from horizons.component.tradepostcomponent import TradePostComponent

class Player(ComponentHolder, WorldObject):
	"""Class representing a player"""

	STATS_UPDATE_INTERVAL = 3 # seconds

	regular_player = True # either a human player or a normal AI player (not trader or pirate)
	component_templates = ({'StorageComponent': {'PositiveStorage': {}}},)


	def __init__(self, session, worldid, name, color, clientid=None, difficulty_level=None):
		"""
		@param session: Session instance
		@param worldid: player's worldid
		@param name: user-chosen name
		@param color: color of player (as Color)
		@param clientid: id of client
		@param inventory: {res: value} that are put in the players inventory
		"""
		if False:
			assert isinstance(session, horizons.session.Session)
		self.session = session
		super(Player, self).__init__(worldid=worldid)
		self.__init(name, color, clientid, difficulty_level)

	def initialize(self, inventory):
		super(Player, self).initialize()
		if inventory:
			for res, value in inventory.iteritems():
				self.get_component(StorageComponent).inventory.alter(res, value)

	def __init(self, name, color, clientid, difficulty_level, settlerlevel=0):
		assert isinstance(color, Color)
		assert isinstance(name, basestring) and name
		try:
			self.name = unicode(name)
		except UnicodeDecodeError:
			# WORKAROUND: this line should be the only unicode conversion here.
			# however, if unicode() gets a parameter, it will fail if the string is already unicode.
			self.name = unicode(name, errors='ignore')
		self.color = color
		self.clientid = clientid
		self.difficulty = DifficultySettings.get_settings(difficulty_level)
		self.settler_level = settlerlevel
		self.stats = None
		assert self.color.is_default_color, "Player color has to be a default color"

		SettlerUpdate.subscribe(self.notify_settler_reached_level)
		NewDisaster.subscribe(self.notify_new_disaster, sender=self)

	@property
	def is_local_player(self):
		return self is self.session.world.player

	def update_stats(self):
		# will only be enabled on demand since it takes a while to calculate
		Scheduler().add_new_object(Callback(self.update_stats), self, run_in = PLAYER.STATS_UPDATE_FREQUENCY)
		self.stats = PlayerStats(self)

	def get_latest_stats(self):
		return self.stats

	@property
	def settlements(self):
		"""Calculate settlements dynamically to save having a redundant list here"""
		return [ settlement for settlement in self.session.world.settlements if
		         settlement.owner == self ]

	def save(self, db):
		super(Player, self).save(db)
		client_id = None if self is not self.session.world.player and \
		                    self.clientid is None else self.clientid

		db("INSERT INTO player(rowid, name, color, client_id, settler_level, difficulty_level) VALUES(?, ?, ?, ?, ?, ?)",
			 self.worldid, self.name, self.color.id, client_id, self.settler_level, self.difficulty.level if self.difficulty is not None else None)

	@classmethod
	def load(cls, session, db, worldid):
		self = cls.__new__(cls)
		self.session = session
		self._load(db, worldid)
		return self

	def _load(self, db, worldid):
		"""This function makes it possible to load playerdata into an already allocated
		Player instance, which is used e.g. in Trader.load"""
		super(Player, self).load(db, worldid)

		color, name, client_id, settlerlevel, difficulty_level = db("SELECT color, name, client_id, settler_level, difficulty_level FROM player WHERE rowid = ?", worldid)[0]
		self.__init(name, Color[color], client_id, difficulty_level, settlerlevel = settlerlevel)

	def notify_unit_path_blocked(self, unit):
		"""Notify the user that a unit stopped moving
		NOTE: this is just a quick fix for a release
		      a signaling concept for such events is planned.
		"""
		self.log.warning("ERROR: UNIT %s CANNOT MOVE ANY FURTHER!", unit)

	def notify_settler_reached_level(self, message):
		"""Settler calls this to notify the player
		@param settler: instance of Settler
		@return: bool, True if actually incremented the level"""
		assert isinstance(message, SettlerUpdate)
		if message.sender.owner is not self:
			return False # was settler of another player
		if message.level > self.settler_level:
			self.settler_level = message.level
			self.session.scenario_eventhandler.check_events(CONDITIONS.settler_level_greater)
			for settlement in self.settlements:
				settlement.level_upgrade(self.settler_level)
			self._changed()
			return True
		else:
			return False

	def notify_mine_empty(self, mine):
		"""The Mine calls this function to let the player know that the mine is empty."""
		pass

	def notify_new_disaster(self, message):
		"""The message bus calls this when a building is 'infected' with a disaster."""
		if self.is_local_player:
			pos = message.building.position.center()
			self.session.ingame_gui.message_widget.add(point=pos, string_id=message.disaster_class.NOTIFICATION_TYPE)

	def end(self):
		self.stats = None
		self.session = None

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

		get_sum = lambda l, attr : sum ( getattr(obj, attr) for obj in l )
		tradeposts = [ s.get_component(TradePostComponent) for s in self.settlements ]
		return Data(
		  running_costs = get_sum(self.settlements, 'cumulative_running_costs'),
		  taxes = get_sum(self.settlements, 'cumulative_taxes'),
		  sell_income = get_sum(tradeposts, 'sell_income'),
		  buy_expenses = get_sum(tradeposts, 'buy_expenses'),
		  balance = get_sum(self.settlements, 'balance'),
		)


class HumanPlayer(Player):
	"""Class for players that physically sit in front of the machine where the game is run"""
	def notify_settler_reached_level(self, message):
		level_up = super(HumanPlayer, self).notify_settler_reached_level(message)
		if level_up:
			# add message and update ingame gui
			self.session.ingame_gui.message_widget.add(point=message.sender.position.center(),
			                                           string_id='SETTLER_LEVEL_UP',
			                                           message_dict={'level': message.level+1})
		return level_up

	def notify_mine_empty(self, mine):
		self.session.ingame_gui.message_widget.add(point=mine.position.center(), string_id='MINE_EMPTY')
