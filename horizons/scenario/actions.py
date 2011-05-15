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

import horizons.main

from horizons.scheduler import Scheduler
from horizons.extscheduler import ExtScheduler
from horizons.util import Callback
from horizons.scenario import CONDITIONS
from horizons.savegamemanager import SavegameManager
from horizons.constants import MESSAGES, AUTO_CONTINUE_CAMPAIGN


###
# Scenario Actions

def show_message(session, *message):
	"""Shows a custom message in the messagewidget. If you pass more than one message, they
	will be shown after each other after a delay"""
	delay_ticks = Scheduler().get_ticks(MESSAGES.CUSTOM_MSG_SHOW_DELAY)
	visible_ticks = Scheduler().get_ticks(MESSAGES.CUSTOM_MSG_VISIBLE_FOR)
	delay_iter = 1
	for msg in message:
		Scheduler().add_new_object(Callback(session.ingame_gui.message_widget.add_custom, None, None, \
		                                    msg + '\n'* 30 + 'UHtutorial', visible_for=visible_ticks), \
		                                    None, run_in=delay_iter)
		delay_iter += delay_ticks
		# for the part """ + '\n'* 30 + 'UHtutorial'""" see below comment (#535)

def show_db_message(session, message_id):
	"""Shows a message specified in the db on the ingame message widget"""
	session.ingame_gui.message_widget.add(None, None, message_id)

def write_logbook_entry(session, head, message):
	"""Silently adds an entry to the logbook."""
	msg = message + '\n'* 30 + 'UHtutorial' # this can get removed once ticket 535 is resolved
	session.ingame_gui.logbook.add_entry(unicode(head),unicode(msg))

def show_logbook_entry(session, head, message):
	"""Adds an entry to the logbook and displays it."""
	write_logbook_entry(session, head, message)
	session.ingame_gui.logbook.show()

def show_logbook_entry_delayed(session, head, message, delay=MESSAGES.LOGBOOK_DEFAULT_DELAY):
	"""Show a logbook entry delayed by delay seconds"""
	callback = Callback(show_logbook_entry, session, head, message)
	Scheduler().add_new_object(callback, session.scenario_eventhandler, run_in=Scheduler().get_ticks(delay))

def do_win(session):
	"""Called when player won"""
	session.speed_pause()
	show_db_message(session, 'YOU_HAVE_WON')
	horizons.main.fife.play_sound('effects', "content/audio/sounds/events/szenario/win.ogg")

	continue_playing = False
	if session.campaign is None or not AUTO_CONTINUE_CAMPAIGN:
		continue_playing = session.gui.show_popup(_("You have won!"), \
		                                          _("You have completed this scenario. " +
		                                            "Do you want to continue playing?"), \
		                                          show_cancel_button=True)
	if not continue_playing:
		if session.campaign:
			# TODO : present a scenario choosing Gui to the user
			SavegameManager.mark_scenario_as_won(session.campaign)
			ExtScheduler().add_new_object(Callback(SavegameManager.load_next_scenario, session.campaign), SavegameManager, run_in=1)
		else:
			Scheduler().add_new_object(Callback(session.gui.quit_session, force=True), session, run_in=0)
	else:
		session.speed_unpause()


def do_lose(session):
	"""Called when player lost"""
	show_message(session, 'You failed the scenario.')
	horizons.main.fife.play_sound('effects', 'content/audio/sounds/events/szenario/loose.ogg')
	# drop events after this event
	Scheduler().add_new_object(session.scenario_eventhandler.drop_events, session.scenario_eventhandler)

def set_var(session, name, value):
	session.scenario_eventhandler._scenario_variables[name] = value
	check_callback = Callback(session.scenario_eventhandler.check_events, CONDITIONS.var_eq)
	Scheduler().add_new_object(check_callback, session.scenario_eventhandler)

def wait(session, time):
	delay = Scheduler().get_ticks(time)
	session.scenario_eventhandler.sleep(delay)


