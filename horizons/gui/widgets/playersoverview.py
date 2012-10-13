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

from fife.extensions.pychan import widgets

from horizons.gui.widgets.statswidget import StatsWidget
from horizons.util.python import decorators

class PlayersOverview(StatsWidget):
	"""Widget that shows the scores of every player in the game."""

	widget_file_name = 'players_overview.xml'

	def __init__(self, session):
		super(PlayersOverview, self).__init__(session)
		# this is supposed to run on the tick after the stats update

	def refresh(self):
		super(PlayersOverview, self).refresh()
		for player in sorted(self.session.world.players, key = lambda player: (-player.get_latest_stats().total_score, player.worldid)):
			self._add_line_to_gui(player)
		self._content_vbox.adaptLayout()

	def _add_line_to_gui(self, player):
		stats = player.get_latest_stats()

		emblem = widgets.Label(name = 'emblem_%d' % player.worldid, text=u"   ")
		emblem.background_color = player.color
		emblem.min_size = (12, 20)

		name = widgets.Label(name = 'player_%d' % player.worldid)
		name.text = player.name
		name.min_size = (108, 20)

		money_score = widgets.Label(name = 'money_score_%d' % player.worldid)
		money_score.text = unicode(stats.money_score)
		money_score.min_size = (60, 20)

		land_score = widgets.Label(name = 'land_score_%d' % player.worldid)
		land_score.text = unicode(stats.land_score)
		land_score.min_size = (50, 20)

		resource_score = widgets.Label(name = 'resource_score_%d' % player.worldid)
		resource_score.text = unicode(stats.resource_score)
		resource_score.min_size = (90, 20)

		building_score = widgets.Label(name = 'building_score_%d' % player.worldid)
		building_score.text = unicode(stats.building_score)
		building_score.min_size = (70, 20)

		settler_score = widgets.Label(name = 'settler_score_%d' % player.worldid)
		settler_score.text = unicode(stats.settler_score)
		settler_score.min_size = (60, 20)

		unit_score = widgets.Label(name = 'unit_score_%d' % player.worldid)
		unit_score.text = unicode(stats.unit_score)
		unit_score.min_size = (50, 20)

		total_score = widgets.Label(name = 'total_score_%d' % player.worldid)
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
		self._content_vbox.addChild(hbox)

decorators.bind_all(PlayersOverview)
