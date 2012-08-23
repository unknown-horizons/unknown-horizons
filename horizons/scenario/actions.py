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

import math

import horizons.main

from horizons.scheduler import Scheduler
from horizons.util import Callback, WorldObject, Point, Circle, Registry
from horizons.command.unit import CreateUnit
from horizons.scenario import CONDITIONS
from horizons.savegamemanager import SavegameManager
from horizons.constants import MESSAGES, AUTO_CONTINUE_CAMPAIGN
from horizons.command.game import PauseCommand, UnPauseCommand
from horizons.messaging import SettlerUpdate
from horizons.component.storagecomponent import StorageComponent


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
def show_message(session, type=None, *messages):
	"""Shows a message with custom text in the messagewidget.
	If you pass more than one message, they are shown simultaneously."""
	visible_ticks = Scheduler().get_ticks(MESSAGES.CUSTOM_MSG_VISIBLE_FOR)
	
	return [session.ingame_gui.message_widget.add_custom(point=None, messagetext=msg, msg_type=type, visible_for=visible_ticks)
	        for msg in messages]

@register(name='db_message')
def show_db_message(session, database_message_id):
	"""Shows a message with predefined text in the messagewidget."""
	session.ingame_gui.message_widget.add(point=None, string_id=database_message_id)

@register(name='logbook')
def show_logbook_entry_delayed(session, *parameters):
	"""Shows a logbook entry and opens the logbook after 'delay' seconds.
	Displays a YAML-defined notification message on logbook close.

	Set delay=0 for instant appearing.
	#TODO get *delay* parameter working again, it is currently not implemented!
	@param parameters: arbitrary list of logbook parameters, including their values.
	                Check widgets.logbook#add_captainslog_entry for parameter documentation.
	"""
	def write_logbook_entry(session, parameters):
		"""Adds an entry to the logbook and displays it.
		On logbook close, displays a notification message defined in the YAML."""
		session.ingame_gui.logbook.add_captainslog_entry(parameters, show_logbook=True)
	delay = MESSAGES.LOGBOOK_DEFAULT_DELAY
	callback = Callback(write_logbook_entry, session, parameters)
	Scheduler().add_new_object(callback, session.scenario_eventhandler, run_in=Scheduler().get_ticks(delay))

@register(name='win')
def do_win(session):
	"""The player wins the current scenario. If part of a campaign, offers to start the next scenario."""
	PauseCommand().execute(session)
	show_db_message(session, 'YOU_HAVE_WON')
	horizons.main.fife.play_sound('effects', "content/audio/sounds/events/scenario/win.ogg")

	continue_playing = False
	if not session.campaign or not AUTO_CONTINUE_CAMPAIGN:
		continue_playing = session.gui.show_popup(_("You have won!"),
		                                          _("You have completed this scenario.") + u" " +
		                                          _("Do you want to continue playing?"),
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
	"""The player reaches a certain goal in the current scenario."""
	# TODO : if we want, we could make this work in "scenario" mode
	#        to allow the player to reach goals in scenarios even if
	#        no campaign was has been loaded.
	if session.campaign:
		SavegameManager.mark_goal_reached(session.campaign, goal_number)

@register(name='lose')
def do_lose(session):
	"""The player fails the current scenario."""
	show_db_message(session, 'YOU_LOST')
	horizons.main.fife.play_sound('effects', 'content/audio/sounds/events/scenario/lose.ogg')
	# drop events after this event
	Scheduler().add_new_object(session.scenario_eventhandler.drop_events, session.scenario_eventhandler)

@register()
def set_var(session, variable, value):
	"""Assigns values to scenario variables. Overwrites previous assignments to the same variable."""
	session.scenario_eventhandler._scenario_variables[variable] = value
	check_callbacks = Callback.ChainedCallbacks(
	  Callback(session.scenario_eventhandler.check_events, CONDITIONS.var_eq),
	  Callback(session.scenario_eventhandler.check_events, CONDITIONS.var_lt),
	  Callback(session.scenario_eventhandler.check_events, CONDITIONS.var_gt)
	)
	Scheduler().add_new_object(check_callbacks, session.scenario_eventhandler, run_in=0)

@register()
def wait(session, seconds):
	"""Postpones any other scenario events for a certain amount of seconds."""
	delay = Scheduler().get_ticks(seconds)
	session.scenario_eventhandler.sleep(delay)

@register()
def alter_inventory(session, resource, amount):
	"""Alters the inventory of each settlement."""
	for settlement in session.world.settlements:
		if settlement.owner == session.world.player and settlement.warehouse:
			settlement.warehouse.get_component(StorageComponent).inventory.alter(
					resource, amount)

@register()
def highlight_position(session, x, y, play_sound=False, color=(0,0,0)):
	"""Highlights a position on the minimap.
	color is a optional parameter that defines the color of the highlight. """
	session.ingame_gui.minimap.highlight((x,y), color=color)
	if play_sound:
		horizons.main.fife.play_sound('effects', 'content/audio/sounds/ships_bell.ogg')

@register()
def change_increment(session, increment):
	""" Changes the increment of the settlements. """
	for settlement in session.world.settlements:
		if settlement.owner == session.world.player:
			# Settler levels are zero-based!
			SettlerUpdate.broadcast(settlement.warehouse, increment - 1, increment - 1)

@register()
def spawn_ships(session, owner_id, ship_id, number, *position):
	"""
	Creates a number of ships controlled by a certain player around a position on the map.
	@param owner_id: the owner worldid
	@param ship_id: the ship id
	@param number: number of ships to be spawned
	@param position: position around the ships to be spawned
	"""
	center = Point(*position)
	player = WorldObject.get_object_by_id(owner_id)
	# calculate a radius that should fit all the ships
	# if it doesn't fit them all increase the radius
	radius = int(math.sqrt(number))
	while number != 0:
		for point in Circle(center, radius):
			if (point.x, point.y) in session.world.ship_map \
				or session.world.get_island(point) is not None:
				continue
			CreateUnit(owner_id, ship_id, point.x, point.y)(issuer=player)
			number -= 1
			if number == 0:
				break
		radius += 1
