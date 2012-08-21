# -.- coding: utf-8 -.-
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

""" This file contains a list of quotes and gameplay tips
that are displayed while loading a game

! NOTE: Try to use not more than 4 lines in a quote/gameplay tip !
"""
from horizons.constants import TIER

# Fun Quotes should not be translated...
FUN_QUOTES = {
	'name': _("Quotes"),
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
	    "Travel beyond the horizon and discover unknown worlds!"
    ]
}

GAMEPLAY_TIPS = {
	'name': _("Gameplay Tips"),
	'items': [
	    _("Press 'ESC' to access Game Menu."),
	    _("Use 'SHIFT' to place multiple buildings."),
	    _("Currently only the first {tier} tiers are playable.").format(
		    tier=TIER.CURRENT_MAX + 1),
	    _("You can pause the game with 'P'."),
	    _("You can drag roads by holding the left mouse button."),
	    _("You can build multiple buildings by holding the 'SHIFT' key."),
	    _("You can increase the happiness of your inhabitants by lowering the taxes."),
	    _("Build fire stations and doctors to protect your inhabitants from fire and disease."),
	    _("Build storage tents to increase your storage capacity.")
    ]
}

""" This are the options you can select in the Settings what type of quotes should be
displayed during load
"""
QUOTES_SETTINGS = (GAMEPLAY_TIPS['name'], FUN_QUOTES['name'], _("Mixed"))
