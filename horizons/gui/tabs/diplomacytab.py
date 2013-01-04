# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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

from horizons.gui.tabs.tabinterface import TabInterface
from horizons.gui.tabs.tabwidget import TabWidget
from horizons.util.python.callback import Callback
from horizons.command.diplomacy import AddAllyPair, AddNeutralPair, AddEnemyPair


class PlayerDiplomacyTab(TabInterface):
	"""
	Diplomacy tab set per player.
	It displays the menu for selecting the status between the local player and the tab's player
	"""
	def __init__(self, player, widget='diplomacy.xml',
	             icon_path='images/tabwidget/emblems/emblem_%s'):
		super(PlayerDiplomacyTab, self).__init__(widget)

		self.local_player = player.session.world.player
		self.player = player
		self.diplomacy = player.session.world.diplomacy
		self.init_values()

		self.widget.findChild(name='headline').text = player.name
		self.widget.mapEvents({
			'ally_label' : self.add_ally,
			'ally_check_box' : self.add_ally,
			'neutral_label' : self.add_neutral,
			'neutral_check_box' : self.add_neutral,
			'enemy_label' : self.add_enemy,
			'enemy_check_box' : self.add_enemy})

		self.check_diplomacy_state()

		#TODO what the heck
		self.path = self.active_path = icon_path % player.color.name

		self.helptext = player.name

	def show(self):
		super(PlayerDiplomacyTab, self).show()
		# if diplomacy is changed by any player, change the checkbox
		self.diplomacy.add_diplomacy_status_changed_listener(Callback(self.check_diplomacy_state))

	def hide(self):
		super(PlayerDiplomacyTab, self).hide()
		self.diplomacy.remove_diplomacy_status_changed_listener(Callback(self.check_diplomacy_state))

	def add_ally(self):
		"""
		Callback for setting ally status between local player and tab's player
		"""
		AddAllyPair(self.player, self.local_player).execute(self.player.session)
		# check the correct checkbox
		self.check_diplomacy_state()

	def add_neutral(self):
		"""
		Callback for setting neutral status between local player and tab's player
		"""
		AddNeutralPair(self.player, self.local_player).execute(self.player.session)
		# check the correct checkbox
		self.check_diplomacy_state()

	def add_enemy(self):
		"""
		Callback for setting enemy status between local player and tab's player
		"""
		AddEnemyPair(self.player, self.local_player).execute(self.player.session)
		# check the correct checkbox
		self.check_diplomacy_state()

	def check_diplomacy_state(self):
		"""
		Checks the box with the diplomacy status between local player and selected player
		"""

		#set all boxes true
		self.widget.distributeData({
			'ally_check_box' : False,
			'neutral_check_box' : False,
			'enemy_check_box' : False})

		#get the name of the selected box
		if self.diplomacy.are_allies(self.local_player, self.player):
			state = 'ally'
		elif self.diplomacy.are_neutral(self.local_player, self.player):
			state = 'neutral'
		else:
			state = 'enemy'

		#check the selected box
		self.widget.distributeData({'%s_check_box' % state : True})


class DiplomacyTab(TabWidget):
	name = "diplomacy_widget"

	def __init__(self, ingame_gui, world):
		players = list(world.players)
		players.append(world.pirate)

		# filter out local player and pirate (if it's disabled)
		players = [p for p in players if p not in (world.player, None)]

		tabs = [PlayerDiplomacyTab(p) for p in players]

		super(DiplomacyTab, self).__init__(ingame_gui, tabs=tabs, name="diplomacy_widget")

	@classmethod
	def is_useable(self, world):
		"""Only useful if there is another player."""
		return not (len(world.players) == 1 and not world.pirate)
