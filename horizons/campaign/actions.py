# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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
from horizons.util import Callback
from horizons.campaign import CONDITIONS


###
# Campaign Actions

def show_message(session, *message):
	"""Shows a custom message in the messagewidget. If you pass more than one message, they
	will be shown after each other after a delay"""
	delay = 6
	delay_ticks = Scheduler().get_ticks(delay)
	delay_iter = 1
	for msg in message:
		Scheduler().add_new_object(Callback(session.ingame_gui.message_widget.add_custom, \
		                                    None, None, msg, visible_for=90), None, runin=delay_iter)
		delay_iter += delay_ticks

def show_db_message(session, message_id):
	"""Shows a message specified in the db on the ingame message widget"""
	session.ingame_gui.message_widget.add(None, None, message_id)

def write_logbook_entry(session, head, message):
	"""Silently adds an entry to the logbook."""
	session.ingame_gui.logbook.add_entry(unicode(head),unicode(message))

def show_logbook_entry(session, head, message):
	"""Adds an entry to the logbook and displays it."""
	session.ingame_gui.logbook.add_entry(unicode(head),unicode(message))
	session.ingame_gui.logbook.show()

def do_win(session):
	"""Called when player won"""
	session.speed_pause()
	show_db_message(session, 'YOU_HAVE_WON')
	horizons.main.fife.play_sound('effects', "content/audio/sounds/events/szenario/win.ogg")

	continue_playing = session.gui.show_popup(_("You have won!"), \
	                                          _("You have completed this scenario. " +
	                                            "Do you want to continue playing?"), \
	                                          show_cancel_button=True)
	if not continue_playing:
		Scheduler().add_new_object(Callback(session.gui.quit_session, force=True), session, runin=0)
	else:
		session.speed_unpause()


def do_lose(session):
	"""Called when player lost"""
	show_message(session, 'You failed the scenario.')
	horizons.main.fife.play_sound('effects', 'content/audio/sounds/events/szenario/loose.ogg')
	# drop events after this event
	Scheduler().add_new_object(session.campaign_eventhandler.drop_events, session.campaign_eventhandler)

def set_var(session, name, value):
	session.campaign_eventhandler._scenario_variables[name] = value
	check_callback = Callback(session.campaign_eventhandler.check_events, CONDITIONS.var_eq)
	Scheduler().add_new_object(check_callback, session.campaign_eventhandler)

def wait(session, time):
	delay = Scheduler().get_ticks(time)
	session.campaign_eventhandler.sleep(delay)


