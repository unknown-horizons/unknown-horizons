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

import tempfile
import os

import horizons.main

from horizons.constants import BUILDINGS, PRODUCTION
from horizons.world.production.producer import Producer
from tests.gui import TestFinished, gui_test



@gui_test(use_fixture='boatbuilder', timeout=120)
def test_ticket_1224(gui):
	"""
	Boat builder running costs are inconsistent.
	"""
	yield # test needs to be a generator for now

	settlement = gui.session.world.player.settlements[0]
	boatbuilder = settlement.buildings_by_id[BUILDINGS.BOAT_BUILDER][0]

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	def running_costs():
		c = gui.find(name='BB_main_tab')
		return c.findChild(name='running_costs').text

	# Check (inactive) running costs
	assert running_costs() == '10', "Expected 10, got %s" % running_costs()

	# Select trade ships tab
	gui.trigger('tab_base', '1/action/default')

	# Build huker
	gui.trigger('boatbuilder_trade', 'BB_build_trade_1/action/default')

	# Wait until production starts
	producer = boatbuilder.get_component(Producer)
	while producer._get_current_state() != PRODUCTION.STATES.producing:
		yield

	# Check (active) running costs
	assert running_costs() == '25', "Expected 25, got %s" % running_costs()

	yield TestFinished


@gui_test(use_fixture='boatbuilder', timeout=120)
def test_ticket_1294(gui):
	"""
	Boatbuilder crash with out of order finishing.
	"""
	yield # test needs to be a generator for now

	settlement = gui.session.world.player.settlements[0]
	boatbuilder = settlement.buildings_by_id[BUILDINGS.BOAT_BUILDER][0]

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	# Select trade ships tab
	gui.trigger('tab_base', '1/action/default')

	# Build huker
	gui.trigger('boatbuilder_trade', 'BB_build_trade_1/action/default')

	# Pause huker construction
	gui.trigger('BB_main_tab', 'toggle_active_active/action/default')

	# Select war ships tab
	gui.trigger('tab_base', '2/action/default')

	# Build frigate
	gui.trigger('boatbuilder_war1', 'BB_build_war1_1/action/default')

	# Wait until production ends
	producer = boatbuilder.get_component(Producer)
	while len(producer.get_productions()) > 1:
		yield

	# Unpause huker construction
	gui.trigger('BB_main_tab', 'toggle_active_inactive/action/default')

	while len(producer.get_productions()) > 0:
		yield

	yield TestFinished


@gui_test(use_fixture='boatbuilder', timeout=60)
def test_remove_from_queue(gui):
	"""
	Boatbuilder crashes when canceling a ship in the queue.
	"""
	yield # test needs to be a generator for now

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	# Select trade ships tab
	gui.trigger('tab_base', '1/action/default')

	# Build huker
	gui.trigger('boatbuilder_trade', 'BB_build_trade_1/action/default')

	# Select war ships tab
	gui.trigger('tab_base', '2/action/default')

	# Build frigate
	gui.trigger('boatbuilder_war1', 'BB_build_war1_1/action/default')

	# Cancel queue -> crash
	gui.trigger('BB_main_tab', 'queue_elem_0/mouseClicked/default')

	yield TestFinished

@gui_test(use_fixture='boatbuilder', timeout=60)
def test_cancel_ticket_1424(gui):
	"""
	Boatbuilder crashes when canceling a ship build.
	"""
	yield # test needs to be a generator for now

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	# Select trade ships tab
	gui.trigger('tab_base', '1/action/default')

	# Build huker
	gui.trigger('boatbuilder_trade', 'BB_build_trade_1/action/default')

	# Select war ships tab
	gui.trigger('tab_base', '2/action/default')

	# Build frigate
	gui.trigger('boatbuilder_war1', 'BB_build_war1_1/action/default')

	# Cancel build completely -> crash
	gui.trigger('BB_main_tab', 'BB_cancel_button/mouseClicked/default')


	yield TestFinished

@gui_test(use_fixture='boatbuilder', timeout=60)
def test_save_load_ticket_1421(gui):
	"""
	Boatbuilder crashes when saving/loading while a ship is being produced.
	"""
	yield # test needs to be a generator for now

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	# Select trade ships tab
	gui.trigger('tab_base', '1/action/default')

	# Build huker
	gui.trigger('boatbuilder_trade', 'BB_build_trade_1/action/default')

	# Select war ships tab
	gui.trigger('tab_base', '2/action/default')

	# Build frigate
	gui.trigger('boatbuilder_war1', 'BB_build_war1_1/action/default')

	fd, filename = tempfile.mkstemp()
	os.close(fd)

	assert gui.session.save(savegamename=filename)

	horizons.main.load_game( savegame=filename )

	yield TestFinished


@gui_test(use_fixture='boatbuilder', timeout=120)
def test_ticket_1513(gui):
	"""
	Boat builder costs don't go back to normal after cancelling a ship.
	"""
	yield # test needs to be a generator for now

	settlement = gui.session.world.player.settlements[0]
	boatbuilder = settlement.buildings_by_id[BUILDINGS.BOAT_BUILDER][0]

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	def running_costs():
		c = gui.find(name='BB_main_tab')
		return c.findChild(name='running_costs').text

	# Check (inactive) running costs
	assert running_costs() == '10', "Expected 10, got %s" % running_costs()

	# Select trade ships tab
	gui.trigger('tab_base', '1/action/default')

	# Build huker
	gui.trigger('boatbuilder_trade', 'BB_build_trade_1/action/default')

	# Wait until production starts
	producer = boatbuilder.get_component(Producer)
	while producer._get_current_state() != PRODUCTION.STATES.producing:
		yield

	# Check (active) running costs
	assert running_costs() == '25', "Expected 25, got %s" % running_costs()

	yield

	# Cancel build
	gui.trigger('BB_main_tab', 'BB_cancel_button/mouseClicked/default')

	# Check (inactive) running costs
	assert running_costs() == '10', "Expected 10, got %s" % running_costs()

	yield TestFinished


@gui_test(use_fixture='boatbuilder', timeout=120)
def test_ticket_1514(gui):
	"""
	Cancelling a ship doesn't update the ship builder's tab.
	"""
	yield # test needs to be a generator for now

	settlement = gui.session.world.player.settlements[0]
	boatbuilder = settlement.buildings_by_id[BUILDINGS.BOAT_BUILDER][0]

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	# nothing beeing build, no cancel button visible
	assert not gui.find('BB_cancel_button')

	# Select trade ships tab
	gui.trigger('tab_base', '1/action/default')

	# Build huker
	gui.trigger('boatbuilder_trade', 'BB_build_trade_1/action/default')

	assert gui.find('BB_cancel_button')

	# Wait until production starts
	producer = boatbuilder.get_component(Producer)
	while producer._get_current_state() != PRODUCTION.STATES.producing:
		yield

	yield

	# Cancel build
	gui.trigger('BB_main_tab', 'BB_cancel_button/mouseClicked/default')

	# The tab should have changed, no cancel button visible
	assert not gui.find('BB_cancel_button')

	yield TestFinished
