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

import random

import horizons.globals
from horizons.i18n.quotes import GAMEPLAY_TIPS, FUN_QUOTES
from horizons.gui.util import load_uh_widget
from horizons.gui.windows import Window
from horizons.messaging import LoadingProgress


class LoadingScreen(Window):
	"""Show quotes/gameplay tips while loading the game"""

	# how often the LoadingProgress message is send when loading a game,
	# used to update the progress bar
	total_steps = 11

	def __init__(self):
		self._widget = load_uh_widget('loadingscreen.xml')
		self._widget.position_technique = "center:center"

		self._current_step = 0

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

	def hide(self):
		self._current_step = 0
		LoadingProgress.discard(self._update)
		self._widget.hide()

	def on_escape(self):
		"""Hitting Esc should not attempt to close the loading screen.

		See #2018 for what happens else."""
		pass

	def _update(self, message):
		self._current_step += 1

		label = self._widget.findChild(name='loading_stage')
		label.text = unicode(message.stage)
		label.adaptLayout()

		self._widget.findChild(name='loading_progress').progress = (100 * self._current_step) // self.total_steps

		horizons.globals.fife.engine.pump()
