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

from fife.extensions.pychan import widgets

from horizons.util.gui import load_uh_widget
from horizons.scheduler import Scheduler
from horizons.util import Callback

class PlayersOverview(object):
	"""
	Widget that shows scores of all players in the game
	"""

	def __init__(self, session):
		super(PlayersOverview, self).__init__()
		self.session = session
		self._initialised = False
		Scheduler().add_new_object(Callback(self._refresh_tick), self, run_in = 2) # this is supposed to run on the tick after the stats update

	def _refresh_tick(self):
		if self._initialised:
			self.refresh()
		Scheduler().add_new_object(Callback(self._refresh_tick), self, run_in = self.session.world.player.stats_update_ticks)

	def show(self):
		self._gui.show()

	def hide(self):
		self._gui.hide()

	def refresh(self):
		self._clear_entries()
		for player in self.session.world.players:
			self._add_player_line_to_gui(self._gui.findChild(name='players_vbox'), player)

	def is_visible(self):
		return self._gui.isVisible()

	def toggle_visibility(self):
		if not self._initialised:
			self._initialised = True
			self._init_gui()
		if self.is_visible():
			self.hide()
		else:
			self.show()

	def _add_player_line_to_gui(self, gui, player):
		stats = player.get_latest_stats()

		emblem = widgets.Label(name='emblem_%d' % player.worldid, text=u"   ")
		emblem.background_color = player.color
		emblem.min_size = (12, 20)

		name = widgets.Label(name='player_%d' % player.worldid)
		name.text = unicode(player.name)
		name.min_size = (108, 20)

		money_score = widgets.Label(name='money_score_%d' % player.worldid)
		money_score.text = unicode(stats.money_score)
		money_score.min_size = (60, 20)

		land_score = widgets.Label(name='land_score_%d' % player.worldid)
		land_score.text = unicode(stats.land_score)
		land_score.min_size = (50, 20)

		resource_score = widgets.Label(name='resource_score_%d' % player.worldid)
		resource_score.text = unicode(stats.resource_score)
		resource_score.min_size = (90, 20)

		building_score = widgets.Label(name='building_score_%d' % player.worldid)
		building_score.text = unicode(stats.building_score)
		building_score.min_size = (70, 20)

		settler_score = widgets.Label(name='settler_score_%d' % player.worldid)
		settler_score.text = unicode(stats.settler_score)
		settler_score.min_size = (60, 20)

		unit_score = widgets.Label(name='unit_score_%d' % player.worldid)
		unit_score.text = unicode(stats.unit_score)
		unit_score.min_size = (50, 20)

		total_score = widgets.Label(name='total_score_%d' % player.worldid)
		total_score.text = unicode(stats.total_score)
		total_score.min_size = (70, 20)

		hbox = widgets.HBox()
		hbox.addChild(emblem)
		hbox.addChild(name)
		hbox.addChild(money_score)
		hbox.addChild(land_score)
		hbox.addChild(resource_score)
		hbox.addChild(building_score)
		hbox.addChild(settler_score)
		hbox.addChild(unit_score)
		hbox.addChild(total_score)
		gui.addChild(hbox)
		gui.adaptLayout()

	def _init_gui(self):
		self._gui = load_uh_widget("players_overview.xml")
		self._gui.mapEvents({
		  'cancelButton' : self.hide,
		  })
		self._gui.position_technique = "automatic"
		self.refresh()

	def _clear_entries(self):
		self._gui.findChild(name='players_vbox').removeAllChildren()
