# Encoding: utf-8
# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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
from horizons.constants import TIER
from horizons.i18n import _lazy
from horizons.gui.util import load_uh_widget
from horizons.gui.windows import Window
from horizons.messaging import LoadingProgress


# list of quotes and gameplay tips that are displayed while loading a game
# NOTE: Try to use not more than 4 lines in a quote/gameplay tip !

FUN_QUOTES = {
	'name': _lazy("Quotes"),
	# Fun Quotes should not be translated...
	'items': [
		"beer, the cause and solution to all problems of humanity",
		"trying is the first step t'wards failing. ",
		"# nobody actually knows how the code below works. ",
		"here be dragons",
		"procrastination is the first step towards getting stuff done",
		"patience is a virtue \n(barra)",
		"you must really, really love to test \n(portal 2)",
		"here be bugs",
		"strength is the capacity to break a chocolate bar into four pieces with your bare hands - and then eat just one of the pieces",
		"If one does not know to which port one is sailing, no wind is favorable",
		"The pessimist complains about the wind; \nthe optimist expects it to change; \nthe realist adjusts the sails",
		"Travel beyond the horizon and discover unknown worlds!",
		u"War… war never changes",
		"Support Unknown Horizons with Cookies!",
		"wow, looks nearly completed \n(Neomex)"
    ]
}


GAMEPLAY_TIPS = {
	'name': _lazy("Gameplay Tips"),
	'items': [
		_lazy("Press 'ESC' to access Game Menu."),
		_lazy("Use 'SHIFT' to place multiple buildings."),
		#TODO: This tip should be removed when all tiers are playable!!
		_lazy("Currently only the first {tier} tiers are playable.").format(
				tier=TIER.CURRENT_MAX + 1),
		_lazy("You can pause the game with 'P'."),
		_lazy("You can drag roads by holding the left mouse button."),
		_lazy("You can build multiple buildings by holding the 'SHIFT' key."),
		_lazy("You can increase the happiness of your inhabitants by lowering the taxes."),
		_lazy("Build fire stations and doctors to protect your inhabitants from fire and disease."),
		_lazy("Build storage tents to increase your storage capacity."),
		_lazy("Make sure every house is in range of a marketplace."),
		_lazy("Press 'T' to make trees transparent.")
	]
}

# This are the options you can select in the Settings what type of quotes should be
# displayed during load
QUOTES_SETTINGS = (GAMEPLAY_TIPS['name'], FUN_QUOTES['name'], _lazy("Mixed"))


def get_random_quote():
	quote_type = int(horizons.globals.fife.get_uh_setting("QuotesType"))
	if quote_type == 2:
		quote_type = random.randint(0, 1) # choose a random type

	if quote_type == 0:
		name = GAMEPLAY_TIPS["name"]
		items = GAMEPLAY_TIPS["items"]
	elif quote_type == 1:
		name = FUN_QUOTES["name"]
		items = FUN_QUOTES["items"]

	return name, random.choice(items)


stage_text = {
	# translators: these are descriptions of the current task while loading a game
	'session_create_world': _lazy(u'Starting engine…'),
	'session_index_fish': _lazy(u'Catching fish…'),
	'session_load_gui': _lazy(u'Drawing user interface…'),
	'session_finish': _lazy(u'Activating timer…'),
	'load_objects': _lazy(u'Chomping game data…'),
	'world_load_map': _lazy(u'Shaping islands…'),
	'world_load_buildings': _lazy(u'Preparing blueprints…'),
	'world_init_water': _lazy(u'Filling world with water…'),
	'world_load_units': _lazy(u'Raising animals…'),
	'world_setup_ai': _lazy(u'Convincing AI…'),
	'world_load_stuff': _lazy(u'Burying treasures…'),
}


class LoadingScreen(Window):
	"""Show quotes/gameplay tips while loading the game"""

	# how often the LoadingProgress message is send when loading a game,
	# used to update the progress bar
	total_steps = len(stage_text)

	def __init__(self):
		self._widget = load_uh_widget('loadingscreen.xml')
		self._widget.position_technique = "center:center"

		self._current_step = 0

	def show(self):
		qotl_type_label = self._widget.findChild(name='qotl_type_label')
		qotl_label = self._widget.findChild(name='qotl_label')

		name, quote = get_random_quote()
		qotl_type_label.text = name
		qotl_label.text = quote

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
		label.text = stage_text.get(message.stage, message.stage)
		label.adaptLayout()

		self._widget.findChild(name='loading_progress').progress = (100 * self._current_step) // self.total_steps

		horizons.globals.fife.engine.pump()
