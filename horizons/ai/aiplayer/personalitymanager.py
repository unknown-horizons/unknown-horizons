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

import logging
from typing import List

from horizons.ai.aiplayer.personality import DefaultPersonality, OtherPersonality


class PersonalityManager:
	"""This class handles the loading of personality data for the AI players."""

	log = logging.getLogger("ai.aiplayer.personality_manager")

	def __init__(self, player):
		self.player = player
		self._personality = player.session.random.choice(self.available_personalities)
		self.log.info('%s assigned personality %s', player, self._personality.__name__)

	def save(self, db):
		db("INSERT INTO ai_personality_manager(rowid, personality) VALUES(?, ?)", self.player.worldid, self._personality.__module__ + '.' + self._personality.__name__)

	def _load(self, db, player):
		self.player = player
		self._personality = None
		personality = db("SELECT personality FROM ai_personality_manager WHERE rowid = ?", player.worldid)[0][0]
		for personality_class in self.available_personalities:
			if personality == personality_class.__module__ + '.' + personality_class.__name__:
				self._personality = personality_class
		if self._personality is None:
			self.log.debug('%s had invalid personality %s', self.player, personality)
			self._personality = self.player.session.random.choice(self.available_personalities)
		self.log.info('%s loaded with personality %s', self.player, self._personality.__name__)

	@classmethod
	def load(cls, db, player):
		self = cls.__new__(cls)
		self._load(db, player)
		return self

	def get(self, name):
		"""Return a class that contains the relevant personality constants."""
		return getattr(self._personality, name)

	available_personalities = [] # type: List[object]

	@classmethod
	def prepare_personalities_list(cls):
		cls.available_personalities.append(DefaultPersonality)
		cls.available_personalities.append(OtherPersonality)


PersonalityManager.prepare_personalities_list()
