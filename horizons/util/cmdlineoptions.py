#!/usr/bin/env python3

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

import datetime
import optparse
import re


def get_option_parser():
	"""Returns inited OptionParser object"""
	from horizons.constants import VERSION
	p = optparse.OptionParser(usage="%prog [options]", version=VERSION.string())
	p.add_option("-d", "--debug", dest="debug", action="store_true",
	             default=False, help="Enable debug output to stderr and a logfile.")
	p.add_option("--fife-path", dest="fife_path", metavar="<path>",
	             help="Specify the path to FIFE root directory.")
	p.add_option("--restore-settings", dest="restore_settings", action="store_true", default=False,
	             help="Restores the default settings. "
	                  "Useful if Unknown Horizons crashes on startup due to misconfiguration.")
	p.add_option("--mp-master", dest="mp_master", metavar="<ip:port>",
	             help="Specify alternative multiplayer master server.")
	p.add_option("--mp-bind", dest="mp_bind", metavar="<ip:port>",
	             help="Specify network address to bind local network client to. "
	                  "This is useful if NAT holepunching is not working but you can forward a static port.")

	start_uh = optparse.OptionGroup(p, "Starting Unknown Horizons")
	start_uh.add_option("--start-map", dest="start_map", metavar="<map>",
	             help="Starts <map>. <map> is the mapname.")
	start_uh.add_option("--start-random-map", dest="start_random_map", action="store_true",
	             help="Starts a random map.")
	start_uh.add_option("--start-specific-random-map", dest="start_specific_random_map",
	             metavar="<seed>", help="Starts a random map with seed <seed>.")
	start_uh.add_option("--start-scenario", dest="start_scenario", metavar="<scenario>",
	             help="Starts <scenario>. <scenario> is the scenarioname.")
	start_uh.add_option("--start-dev-map", dest="start_dev_map", action="store_true",
	             default=False, help="Starts the development map without displaying the main menu.")
	start_uh.add_option("--load-game", dest="load_game", metavar="<game>",
	             help="Loads a saved game. <game> is the saved game's name.")
	start_uh.add_option("--load-last-quicksave", dest="load_quicksave", action="store_true",
	             help="Loads the last quicksave.")
	start_uh.add_option("--edit-map", dest="edit_map", metavar="<map>",
	             help="Edit map <map>.")
	start_uh.add_option("--edit-game-map", dest="edit_game_map", metavar="<game>",
	             help="Edit the map from the saved game <game>.")
	start_uh.add_option("--no-audio", dest="no_audio", action="store_true", help="Starts UH without sounds.")
	p.add_option_group(start_uh)

	ai_group = optparse.OptionGroup(p, "AI options")
	ai_group.add_option("--ai-players", dest="ai_players", metavar="<ai_players>",
	             type="int", default=0,
	             help="Uses <ai_players> AI players (excludes the possible human-AI hybrid; defaults to 0).")
	ai_group.add_option("--human-ai-hybrid", dest="human_ai", action="store_true",
	             help="Makes the human player a human-AI hybrid (for development only).")
	ai_group.add_option("--force-player-id", dest="force_player_id",
	             metavar="<force_player_id>", type="int", default=None,
	             help="Set the player with id <force_player_id> as the active (human) player.")
	ai_group.add_option("--ai-highlights", dest="ai_highlights", action="store_true",
	             help="Shows AI plans as highlights (for development only).")
	ai_group.add_option("--ai-combat-highlights", dest="ai_combat_highlights", action="store_true",
	             help="Highlights combat ranges for units controlled by AI Players (for development only).")
	p.add_option_group(ai_group)

	dev_group = optparse.OptionGroup(p, "Development options")
	dev_group.add_option("--debug-log-only", dest="debug_log_only", action="store_true",
	             default=False, help="Write debug output only to logfile, not to console. Implies -d.")
	dev_group.add_option("--debug-module", action="append", dest="debug_module",
	             metavar="<module>", default=[],
	             help="Enable logging for a certain logging module (for developing only).")
	dev_group.add_option("--logfile", dest="logfile", metavar="<filename>",
	             help="Writes log to <filename> instead of to the uh-userdir")
	dev_group.add_option("--max-ticks", dest="max_ticks", metavar="<max_ticks>", type="int",
	             help="Run the game for <max_ticks> ticks.")
	dev_group.add_option("--no-freeze-protection", dest="freeze_protection", action="store_false",
	             default=True, help="Disable freeze protection.")
	dev_group.add_option("--string-previewer", dest="stringpreview", action="store_true",
	             default=False, help="Enable the string previewer tool for scenario writers")
	dev_group.add_option("--no-preload", dest="nopreload", action="store_true",
	             default=False, help="Disable preloading while in main menu")
	dev_group.add_option("--game-speed", dest="gamespeed", metavar="<game_speed>", type="float",
	             help="Run the game in the given speed (Values: 0.5, 1, 2, 3, 4, 6, 8, 11, 20)")
	dev_group.add_option("--gui-test", dest="gui_test", metavar="<test>",
	             default=False, help=optparse.SUPPRESS_HELP)
	dev_group.add_option("--gui-log", dest="log_gui", action="store_true",
	             default=False, help="Log gui interactions")
	dev_group.add_option("--sp-seed", dest="sp_seed", metavar="<seed>", type="int",
	             help="Use this seed for singleplayer sessions.")
	dev_group.add_option("--generate-minimap", dest="generate_minimap",
	             metavar="<parameters>", help=optparse.SUPPRESS_HELP)
	dev_group.add_option("--create-mp-game", action="store_true", dest="create_mp_game",
	             help="Create an multiplayer game with default settings.")
	dev_group.add_option("--join-mp-game", action="store_true", dest="join_mp_game",
	             help="Join first multiplayer game.")
	if VERSION.IS_DEV_VERSION:
		dev_group.add_option("--no-atlas-generation", action="store_false", dest="atlas_generation",
	             help="Disable atlas generation.")
	# Add dummy default variables for the DEV_VERSION groups above when in release mode
	p.set_defaults(atlas_generation=True)
	p.add_option_group(dev_group)

	return p


class ManPageFormatter(optparse.HelpFormatter):
	"""Formatter that extracts our huge option list into manpage format.

	Inspired by and mostly copied from this blog post:
	http://andialbrecht.wordpress.com/2009/03/17/creating-a-man-page-with-distutils-and-optparse/
	"""
	def __init__(self, indent_increment=2, max_help_position=24,
			width=72, short_first=1):
		optparse.HelpFormatter.__init__(self,
			indent_increment, max_help_position, width, short_first)

	def _markup(self, text):
		return text.replace('-', r'\-')

	def optmarkup(self, text):
		"""Highlight flags only"""
		replace_with = r'\\fB\1\\fR'
		pattern = r'(--\w*)(?:, )?'
		text = re.sub(pattern, replace_with, text)
		pattern = r'(-\w*)'
		text = re.sub(pattern, replace_with, text)
		return self._markup(text)

	def format_text(self, text):
		return self._markup(text)

	def format_usage(self, usage):
		"""Overridden, else it would print 'options.py usage'."""
		return r'''\
." some portability stuff
.ie \n(.g .ds Aq \(aq
.el       .ds Aq '
." disable hyphenation and justification (adjust text to left margin only)
.nh
.ad l
.SH "NAME"
unknown-horizons \- real-time strategy/simulation game
.SH "SYNOPSIS"
.HP \w'\fBunknown\-horizons\fR\ 'u
\fBunknown\-horizons\fR [{\fB\-h\fR\ |\ \fB\-\-help\fR}]
.SH "DESCRIPTION"
.PP
Isometric 2D real-time strategy/simulation fun.
.br
It puts emphasis on the economy and city building aspects.
.br
Expand your small settlement to a strong and wealthy colony, collect
taxes and supply your inhabitants with valuable goods.
.br
Increase your power with a well balanced economy, with strategic
trade and diplomacy.
.SH "OPTIONS"'''

	def format_heading(self, text):
		"""Format an option group.."""
		if self.level == 0:
			return ''
		return r'''.TP
\fB{}\fR
'''.format(self._markup(text.upper()))

	def format_option(self, option, *args, **kwargs):
		"""Format a single option.

		The base class takes care to replace custom optparse values."""
		result = []
		opts = self.option_strings[option]
		help_text = self.expand_default(option)
		result.append(r'''\
.TP
.B
{}
{}
'''.format(self.optmarkup(opts), self._markup(help_text)))

		return ''.join(result)


if __name__ == '__main__':
	formatter = ManPageFormatter()

	p = get_option_parser()
	p.formatter = formatter

	today = datetime.date.today()
	print(r'''\
'\" t
.\"     Title: unknown-horizons
.\"    Author: The Unknown Horizons Team <team@unknown-horizons.org>
.\"      Date: {0}
.\"  Language: English
.\"
.TH "UNKNOWN\-HORIZONS" "6" "{0}" "unknown-horizons" "Unknown Horizons User Commands"
'''.format(datetime.date.today()))
	p.print_help()

	print(r'''\
.SH "BUGS"
.PP
The bugtracker can be found at \fBhttps://github.com/unknown-horizons/unknown-horizons/issues\fR\&.
.SH "AUTHOR"
.PP
\fBThe Unknown Horizons Team\fR <\&team@unknown-horizons\&.org\&>
.RS 4
.RE
.SH "COPYRIGHT"
.br
Copyright \(co 2008-2017 The Unknown Horizons Team
.br
.PP
Permission is granted to copy, distribute and/or modify this document under the
terms of the GNU General Public License, Version 3 or (at your option) any later
version published by the Free Software Foundation\&.
.sp
''')
