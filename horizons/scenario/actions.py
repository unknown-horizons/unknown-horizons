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

import horizons.main

from horizons.scheduler import Scheduler
from horizons.util import Callback, WorldObject, Point, Circle, Registry
from horizons.command.unit import CreateUnit
from horizons.scenario import CONDITIONS
from horizons.savegamemanager import SavegameManager
from horizons.constants import MESSAGES, AUTO_CONTINUE_CAMPAIGN
from horizons.command.game import PauseCommand, UnPauseCommand


class ACTIONS(object):
	"""Class that holds all available action functions."""
	__metaclass__ = Registry

	@classmethod
	def register_function(cls, func, name=None):
		"""Register action.

		By default, the function's name is used as identifier of the action. You can supply
		a `name` parameter to use instead.
		"""
		cls.registry[name or func.__name__] = func


register = ACTIONS.register


@register(name='message')
def show_message(session, *message):
	"""Shows a custom message in the messagewidget. If you pass more than one message, they
	will be shown after each other after a delay"""
	delay_ticks = Scheduler().get_ticks(MESSAGES.CUSTOM_MSG_SHOW_DELAY)
	visible_ticks = Scheduler().get_ticks(MESSAGES.CUSTOM_MSG_VISIBLE_FOR)
	delay_iter = 1
	for msg in message:
		Scheduler().add_new_object(Callback(session.ingame_gui.message_widget.add_custom, None, None, \
		                                    msg,  visible_for=visible_ticks), \
		                           None, run_in=delay_iter)
		delay_iter += delay_ticks

@register(name='db_message')
def show_db_message(session, message_id):
	"""Shows a message specified in the db on the ingame message widget"""
	session.ingame_gui.message_widget.add(None, None, message_id)

@register(name='logbook_w')
def write_logbook_entry(session, widgets):
	"""Adds an entry to the logbook and displays it."""
	session.ingame_gui.logbook.add_captainslog_entry(widgets, show_logbook=True)

@register(name='logbook')
def show_logbook_entry_delayed(session, *widgets):
	"""Show a logbook entry delayed by delay seconds.

	Set delay=0 for instant appearing.
	#TODO get *delay* parameter working again
	"""
	delay = MESSAGES.LOGBOOK_DEFAULT_DELAY
	callback = Callback(write_logbook_entry, session, widgets)
	Scheduler().add_new_object(callback, session.scenario_eventhandler, run_in=Scheduler().get_ticks(delay))

@register(name='win')
def do_win(session):
	"""Called when player won"""
	PauseCommand().execute(session)
	show_db_message(session, 'YOU_HAVE_WON')
	horizons.main.fife.play_sound('effects', "content/audio/sounds/events/scenario/win.ogg")

	continue_playing = False
	if not session.campaign or not AUTO_CONTINUE_CAMPAIGN:
		continue_playing = session.gui.show_popup(_("You have won!"), \
		                                          _("You have completed this scenario.") + u" " + \
		                                          _("Do you want to continue playing?"), \
		                                          show_cancel_button=True)
	if not continue_playing:
		if session.campaign:
			SavegameManager.mark_scenario_as_won(session.campaign)
			session.ingame_gui.scenario_chooser.show()
		else:
			Scheduler().add_new_object(Callback(session.gui.quit_session, force=True), session, run_in=0)
	else:
		UnPauseCommand().execute(session)

@register(name='goal_reached')
def goal_reached(session, goal_number):
	"""Called when player reached a goal in a scenario"""
	# TODO : if we want, we could make this work in "scenario" mode
	#        to allow the player to reach goals in scenarios even if
	#        no campaign was has been loaded.
	if session.campaign:
		SavegameManager.mark_goal_reached(session.campaign, goal_number)

@register(name='lose')
def do_lose(session):
	"""Called when player lost"""
	show_message(session, 'You failed the scenario.')
	horizons.main.fife.play_sound('effects', 'content/audio/sounds/events/scenario/loose.ogg')
	# drop events after this event
	Scheduler().add_new_object(session.scenario_eventhandler.drop_events, session.scenario_eventhandler)

@register()
def set_var(session, name, value):
	session.scenario_eventhandler._scenario_variables[name] = value
	check_callback = Callback(session.scenario_eventhandler.check_events, CONDITIONS.var_eq)
	Scheduler().add_new_object(check_callback, session.scenario_eventhandler)

@register()
def wait(session, time):
	delay = Scheduler().get_ticks(time)
	session.scenario_eventhandler.sleep(delay)

@register()
def spawn_ships(session, owner, id, number, *position):
	"""
	spawns a number of ships for owner
	@param owner: the owner worldid
	@param id: the ship id
	@param number: number of ships to be spawned
	@param position: position around the ships to be spawned
	"""
	center = Point(*position)
	player = WorldObject.get_object_by_id(owner)
	import math
	# calculate a radius that should fit all the ships
	# if it doesn't fit them all increase the radius
	radius = int(math.sqrt(number))
	while number != 0:
		for point in Circle(center, radius):
			if (point.x, point.y) in session.world.ship_map \
				or session.world.get_island(point) is not None:
				continue
			CreateUnit(owner, id, point.x, point.y)(issuer=player)
			number -= 1
			if number == 0:
				break
		radius += 1
