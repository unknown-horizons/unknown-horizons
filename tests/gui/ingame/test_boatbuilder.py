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

from horizons.constants import BUILDINGS, PRODUCTION, GAME_SPEED
from horizons.world.production.producer import Producer
from tests.gui import TestFinished, gui_test


@gui_test(use_fixture='boatbuilder_1224')
def test_ticket_1224(gui):
	"""
	Boat builder running costs are inconsistent.
	"""
	yield # test needs to be a generator for now

	settlement = gui.session.world.player.settlements[0]
	boatbuilder = settlement.get_buildings_by_id(BUILDINGS.BOATBUILDER_CLASS)[0]

	gui.select([boatbuilder])

	def running_costs():
		c = gui.find(name='BB_main_tab')
		return c.findChild(name='running_costs').text

	# Check (inactive) running costs
	assert running_costs() == '10', "Expected 10, got %s" % running_costs()

	# Select trade ships tab
	c = gui.find(name='tab_base')
	gui.trigger(c, '1/action/default')

	# Build huker
	c = gui.find(name='boatbuilder_trade')
	gui.trigger(c, 'BB_build_trade_1/action/default')

	# Wait until production starts
	producer = boatbuilder.get_component(Producer)
	while producer._get_current_state() != PRODUCTION.STATES.producing:
		yield

	# Check (active) running costs
	assert running_costs() == '25', "Expected 25, got %s" % running_costs()

	yield TestFinished


@gui_test(use_fixture='boatbuilder_1224')
def test_ticket_1294(gui):
	"""
	Boat builder running costs are inconsistent.
	"""
	yield # test needs to be a generator for now

	settlement = gui.session.world.player.settlements[0]
	boatbuilder = settlement.get_buildings_by_id(BUILDINGS.BOATBUILDER_CLASS)[0]

	gui.select([boatbuilder])

	# Select trade ships tab
	c = gui.find(name='tab_base')
	gui.trigger(c, '1/action/default')

	# Build huker
	c = gui.find(name='boatbuilder_trade')
	gui.trigger(c, 'BB_build_trade_1/action/default')

	# Pause huker construction
	c = gui.find(name='BB_main_tab')
	gui.trigger(c, 'toggle_active_active/action/default')

	# Select war ships tab
	c = gui.find(name='tab_base')
	gui.trigger(c, '2/action/default')

	# Build frigate
	c = gui.find(name='boatbuilder_war1')
	gui.trigger(c, 'BB_build_war1_1/action/default')

	gui.session.speed_set(GAME_SPEED.TICK_RATES[-1]) # speed things up a bit

	# Wait until production ends
	producer = boatbuilder.get_component(Producer)
	while producer._get_current_state() != PRODUCTION.STATES.done:
		yield

	# After some seconds it will crash
	for i in xrange(gui.session.timer.get_ticks(5)):
		yield

	yield TestFinished


@gui_test(use_fixture='boatbuilder_1224')
def test_remove_from_queue(gui):
	"""
	Boatbuilder crashes when canceling a ship in the queue.
	"""
	yield # test needs to be a generator for now

	settlement = gui.session.world.player.settlements[0]
	boatbuilder = settlement.get_buildings_by_id(BUILDINGS.BOATBUILDER_CLASS)[0]

	gui.select([boatbuilder])

	# Select trade ships tab
	c = gui.find(name='tab_base')
	gui.trigger(c, '1/action/default')

	# Build huker
	c = gui.find(name='boatbuilder_trade')
	gui.trigger(c, 'BB_build_trade_1/action/default')

	# Select war ships tab
	c = gui.find(name='tab_base')
	gui.trigger(c, '2/action/default')

	# Build frigate
	c = gui.find(name='boatbuilder_war1')
	gui.trigger(c, 'BB_build_war1_1/action/default')

	# Cancel huker -> crash
	c = gui.find(name='BB_main_tab')
	gui.trigger(c, 'queue_container/mouseClicked/default')

	yield TestFinished
