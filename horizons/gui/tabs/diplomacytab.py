# -*- coding: utf-8 -*-
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

from horizons.gui.tabs.tabinterface import TabInterface
from horizons.util import Callback
from horizons.command.diplomacy import AddAllyPair, AddNeutralPair, AddEnemyPair

class DiplomacyTab(TabInterface):
	"""
	Diplomacy tab set per player.
	It displays the menu for selecting the status between the local player and the tab's player
	"""
	def __init__(self, player, widget = 'diplomacy.xml', \
	             icon_path='content/gui/images/tabwidget/emblems/emblem_%s.png'):
		super(DiplomacyTab, self).__init__(widget)

		self.local_player = player.session.world.player
		self.player = player
		self.diplomacy = player.session.world.diplomacy
		self.init_values()

		self.widget.findChild(name='headline').text = unicode(player.name)
		self.widget.mapEvents({
			'ally_label' : self.add_ally,
			'ally_check_box' : self.add_ally,
			'neutral_label' : self.add_neutral,
			'neutral_check_box' : self.add_neutral,
			'enemy_label' : self.add_enemy,
			'enemy_check_box' : self.add_enemy})

		self.check_diplomacy_state()

		color = player.color.name
		self.button_up_image = icon_path % color
		self.button_active_image = icon_path % color
		self.button_down_image = icon_path % color
		self.button_hover_image = icon_path % color
		self.helptext = player.name

		self.widget.stylize("default")
		self.widget.findChild(name="ally_check_box").base_color = 80, 80, 80
		self.widget.findChild(name="enemy_check_box").base_color = 80, 80, 80
		self.widget.findChild(name="neutral_check_box").base_color = 80, 80, 80

	def show(self):
		super(DiplomacyTab, self).show()
		# if diplomacy is changed by any player, change the checkbox
		self.diplomacy.add_diplomacy_status_changed_listener(Callback(self.check_diplomacy_state))

	def hide(self):
		super(DiplomacyTab, self).hide()
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

