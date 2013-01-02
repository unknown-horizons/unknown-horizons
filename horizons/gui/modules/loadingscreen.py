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

import pprint
import random
import time

import horizons.globals
from horizons.i18n.quotes import GAMEPLAY_TIPS, FUN_QUOTES
from horizons.gui.util import load_uh_widget
from horizons.gui.windows import Window
from horizons.messaging import LoadingProgress


# run game with LoadingScreen.profile True to get these values
LOAD_PROGRESS = {
	'finish': 100,
	'load_objects': 0,
	'session_create_world': 4,
	'session_index_fish': 64,
	'session_load_gui': 90,
	'start': 0,
	'world_init_water': 22,
	'world_load_buildings': 17,
	'world_load_map': 4,
	'world_load_stuff': 24,
	'world_load_units': 24
}


class LoadingScreen(Window):
	"""Show quotes/gameplay tips while loading the game"""
	profile = False

	def __init__(self):
		self._widget = load_uh_widget('loadingscreen.xml')
		self._widget.position_technique = "center:center"

		self._times = []

	def show(self):
		qotl_type_label = self._widget.findChild(name='qotl_type_label')
		qotl_label = self._widget.findChild(name='qotl_label')
		quote_type = int(horizons.globals.fife.get_uh_setting("QuotesType"))
		if quote_type == 2:
			quote_type = random.randint(0, 1) # choose a random type

		if quote_type == 0:
			name = GAMEPLAY_TIPS["name"]
			items = GAMEPLAY_TIPS["items"]
		elif quote_type == 1:
			name = FUN_QUOTES["name"]
			items = FUN_QUOTES["items"]

		qotl_type_label.text = unicode(name)
		qotl_label.text = unicode(random.choice(items)) # choose a random quote / gameplay tip

		self._widget.show()
		LoadingProgress.subscribe(self._update)

		if self.profile:
			self._times.append(('start', time.time()))

	def hide(self):
		LoadingProgress.unsubscribe(self._update)
		self._widget.hide()

		if self.profile:
			start = self._times[0][1]
			total = self._times[-1][1] - start
			pprint.pprint(dict([(stage, int(100 * (t - start) / total)) for (stage, t) in self._times]))

	def _update(self, message):
		if self.profile:
			self._times.append((message.stage, time.time()))

		label = self._widget.findChild(name='loading_label')
		label.text = unicode(message.stage)
		label.adaptLayout()

		if not self.profile:
			self._widget.findChild(name='progress').progress = LOAD_PROGRESS[message.stage]

		horizons.globals.fife.engine.pump()
