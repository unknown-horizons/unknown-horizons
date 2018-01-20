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

import math

import horizons.globals
from horizons.command.game import PauseCommand, UnPauseCommand
from horizons.command.unit import CreateUnit
from horizons.constants import MESSAGES
from horizons.i18n import gettext as T
from horizons.messaging import SettlerUpdate
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback
from horizons.util.python.registry import Registry
from horizons.util.shapes import Circle, Point
from horizons.util.worldobject import WorldObject

from .conditions import CONDITIONS


class ActionsRegistry(Registry):
	"""Class that holds all available action functions."""
	def register_function(self, func, name=None):
		"""Register action.

		By default, the function's name is used as identifier of the action. You can supply
		a `name` parameter to use instead.
		"""
		self.registry[name or func.__name__] = func


ACTIONS = ActionsRegistry()
register = ACTIONS.register


@register(name='message')
def show_message(session, type=None, *messages):
	"""Shows a message with custom text in the messagewidget.
	If you pass more than one message, they are shown simultaneously."""
	visible_ticks = Scheduler().get_ticks(MESSAGES.CUSTOM_MSG_VISIBLE_FOR)

	return [session.ingame_gui.message_widget.add_custom(msg, msg_type=type, visible_for=visible_ticks)
	        for msg in messages]


@register(name='db_message')
def show_db_message(session, database_message_id):
	"""Shows a message with predefined text in the messagewidget."""
	session.ingame_gui.message_widget.add(database_message_id)


@register(name='logbook')
def show_logbook_entry_delayed(session, *parameters):
	"""Shows a logbook entry and opens the logbook after some seconds.
	Displays a YAML-defined notification message on logbook close.

	@param parameters: list of logbook parameters, including their values.
	See widgets.logbook:add_captainslog_entry for parameter documentation.
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
	"""The player wins the current scenario."""
	PauseCommand().execute(session)
	show_db_message(session, 'YOU_HAVE_WON')
	horizons.globals.fife.play_sound('effects', "content/audio/sounds/events/scenario/win.ogg")

	continue_playing = session.ingame_gui.open_popup(T("You have won!"),
	                                                 T("You have completed this scenario.") + " " +
	                                                 T("Do you want to continue playing?"),
	                                                 show_cancel_button=True)
	if not continue_playing:
		Scheduler().add_new_object(session.quit, session, run_in=0)
	else:
		UnPauseCommand().execute(session)


@register(name='goal_reached')
def goal_reached(session, goal_number):
	"""The player reaches a certain goal in the current scenario."""
	# This method is kept to make some tests happy.
	pass


@register(name='lose')
def do_lose(session):
	"""The player fails the current scenario."""
	show_db_message(session, 'YOU_LOST')
	horizons.globals.fife.play_sound('effects', 'content/audio/sounds/events/scenario/lose.ogg')
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
	# NOTE avoid circular import
	from horizons.component.storagecomponent import StorageComponent
	for settlement in session.world.settlements:
		if settlement.owner == session.world.player and settlement.warehouse:
			settlement.warehouse.get_component(StorageComponent).inventory.alter(
					resource, amount)


@register()
def highlight_position(session, where, play_sound=False, color=(0, 0, 0)):
	"""Highlights a position on the minimap.
	where: (x, y) coordinate tuple
	color is a optional parameter that defines the color of the highlight. """
	session.ingame_gui.minimap.highlight(where, color=color)
	if play_sound:
		horizons.globals.fife.play_sound('effects', 'content/audio/sounds/ships_bell.ogg')


@register(name='change_increment')
def change_tier(session, tier):
	""" Changes the tier of the settlements. """
	for settlement in session.world.settlements:
		if settlement.owner == session.world.player:
			# Settler levels are zero-based!
			SettlerUpdate.broadcast(settlement.warehouse, tier - 1, tier - 1)


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
