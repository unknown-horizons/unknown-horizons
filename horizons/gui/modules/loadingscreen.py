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


class LoadingScreen(Window):
	"""Show quotes/gameplay tips while loading the game"""

	def __init__(self):
		self._widget = load_uh_widget('loadingscreen.xml')
		self._widget.position_technique = "center:center"

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

	def hide(self):
		self._widget.hide()

	def isVisible(self):
		# TODO remote me once window manager works
		return self._widget.isVisible()
