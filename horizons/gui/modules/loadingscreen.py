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

import random

import horizons.globals
from horizons.constants import TIER
from horizons.ext.speaklater import make_lazy_string
from horizons.gui.util import load_uh_widget
from horizons.gui.windows import Window
from horizons.i18n import gettext as T, gettext_lazy as LazyT
from horizons.messaging import LoadingProgress

# list of quotes and gameplay tips that are displayed while loading a game
# NOTE: Try to use not more than 4 lines in a quote/gameplay tip !

FUN_QUOTES = {
	'name': LazyT("Quotes"),
	# Fun Quotes should not be translated...
	'items': [
		"Beer, the cause and solution to all problems of humanity.",
		"Trying is the first step t'wards failing.",
		"# nobody actually knows how the code below works.",
		"Here are dragons.",
		"Procrastination is the first step towards getting stuff done.",
		"Patience is a virtue. \n(barra)",
		"You must really, really love to test. \n(portal 2)",
		"Here are bugs.",
		"Strength is the capacity to break a chocolate bar into four pieces with your bare hands - and then eat just one of the pieces.",
		"If one does not know to which port one is sailing, no wind is favorable.",
		"The pessimist complains about the wind; \nthe optimist expects it to change; \nthe realist adjusts the sails.",
		"Travel beyond the horizon and discover unknown worlds!",
		"War… war never changes.",
		"Support Unknown Horizons with Cookies!",
		"Wow, looks nearly completed. \n(Neomex)",
		"Anchor is missing ...",
		"Campfire is lighted.",
		"The fish was as large as the whole island.",
		"Bugs are for your personal fun.",
		"Your game is unique. Please wait.",
		"Take it easy, the shore is near.",
		"Come on, let's discover new land."
    ]
}


GAMEPLAY_TIPS = {
	'name': LazyT("Gameplay Tips"),
	'items': [
		LazyT("Press 'ESC' to access Game Menu."),
		LazyT("Use 'SHIFT' to place multiple buildings."),
		#TODO: This tip should be removed when all tiers are playable!!
		make_lazy_string(lambda: T("Currently only the first {tier} tiers are playable.").format(tier=TIER.CURRENT_MAX + 1)),
		LazyT("You can pause the game with 'P'."),
		LazyT("You can drag roads by holding the left mouse button."),
		LazyT("You can build multiple buildings by holding the 'SHIFT' key."),
		LazyT("You can increase the happiness of your inhabitants by lowering the taxes."),
		LazyT("Build fire stations and doctors to protect your inhabitants from fire and disease."),
		LazyT("Build storage tents to increase your storage capacity."),
		LazyT("Make sure every house is in range of a marketplace."),
		LazyT("Press 'T' to make trees transparent."),
		LazyT("Build storage tents and lookouts to expand your settlement range."),
		LazyT("To easily see whether the pavilion's range cover all your tents, select it from the build menu and hover it over your existing pavilion. Uncovered tents are shown in yellow. It's a good idea to build a new pavilion in their neighborhood."),
		LazyT("Make singleplayer more fun with additional computer players by increasing 'AI players' when starting a new game."),
		LazyT("First steps are easier by looking at how AI players are setting up their settlement."),
		LazyT("Want funny quotes only? Change the quote types shown here in the settings menu on the game page."),
		LazyT("A marketplace links your buildings like a road.")
	]
}

# This are the options you can select in the Settings what type of quotes should be
# displayed during load
QUOTES_SETTINGS = (GAMEPLAY_TIPS['name'], FUN_QUOTES['name'], LazyT("Mixed"))


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
	'session_create_world': LazyT('Starting engine…'),
	'session_index_fish': LazyT('Catching fish…'),
	'session_load_gui': LazyT('Drawing user interface…'),
	'session_finish': LazyT('Activating timer…'),
	'load_objects': LazyT('Chomping game data…'),
	'world_load_map': LazyT('Shaping islands…'),
	'world_load_buildings': LazyT('Preparing blueprints…'),
	'world_init_water': LazyT('Filling world with water…'),
	'world_load_units': LazyT('Raising animals…'),
	'world_setup_ai': LazyT('Convincing AI…'),
	'world_load_stuff': LazyT('Burying treasures…'),
}


class LoadingScreen(Window):
	"""Show quotes/gameplay tips while loading the game"""

	# how often the LoadingProgress message is send when loading a game,
	# used to update the progress bar
	total_steps = len(stage_text)

	def __init__(self):
		(width, height) = horizons.globals.fife.get_fife_setting('ScreenResolution').split('x')

		res_width = int(width)
		res_height = int(height)

		self._widget = load_uh_widget('loadingscreen.xml')

		loadingscreen = self._widget.findChild(name='loadingscreen')
		loadingscreen.size = res_width, res_height

		# centered vertically and horizontally
		loading_box = self._widget.findChild(name='loading_box')
		loading_box.position = (
			(res_width - loading_box.size[0]) // 2,
			(res_height - loading_box.size[1]) // 2
		)

		# centered horizontally, aligned at bottom
		quote_area = self._widget.findChild(name='quote_area')

		# set size to visible size, to make aligning children resolution independent
		quote_area.size = (
			min(res_width, quote_area.size[0]),
			min(res_height, quote_area.size[1])
		)

		quote_area.position = (
			(res_width - quote_area.size[0]) // 2,
			res_height - quote_area.size[1]
		)

		loading_stage = self._widget.findChild(name='loading_stage')
		loading_stage.position = 150, 90

		quote_type_label = self._widget.findChild(name='quote_type_label')
		quote_label = self._widget.findChild(name='quote_label')

		quote_type_label.position = (
			quote_area.size[0] - 600,
			80
		)
		quote_label.position = (
			quote_area.size[0] - 600,
			90
		)

		self._current_step = 0

	def show(self):
		quote_type_label = self._widget.findChild(name='quote_type_label')
		quote_label = self._widget.findChild(name='quote_label')

		name, quote = get_random_quote()
		quote_type_label.text = name
		quote_label.text = quote

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

		self._widget.findChild(name='loading_box_progress').progress = (100 * self._current_step) // self.total_steps

		horizons.globals.fife.engine.pump()
