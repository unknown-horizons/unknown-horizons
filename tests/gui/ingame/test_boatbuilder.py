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

from horizons.constants import BUILDINGS, PRODUCTION, UNITS
from horizons.world.production.producer import Producer
from tests.gui import gui_test
from tests.gui.helper import saveload


@gui_test(use_fixture='boatbuilder', timeout=120)
def test_ticket_1224(gui):
	"""
	Boat builder running costs are inconsistent.
	"""

	settlement = gui.session.world.player.settlements[0]
	boatbuilder = settlement.buildings_by_id[BUILDINGS.BOAT_BUILDER][0]

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	def running_costs():
		c = gui.find(name='UB_main_tab')
		return c.findChild(name='running_costs').text

	# Check (inactive) running costs
	assert running_costs() == '10', "Expected 10, got {}".format(running_costs())

	# Select trade ships tab
	gui.trigger('tab_base/1')

	# Build huker
	gui.trigger('boatbuilder_showcase/ok_0')

	# Wait until production starts
	producer = boatbuilder.get_component(Producer)
	while producer._get_current_state() != PRODUCTION.STATES.producing:
		gui.run()

	# Check (active) running costs
	assert running_costs() == '25', "Expected 25, got {}".format(running_costs())


@gui_test(use_fixture='boatbuilder', timeout=120)
def test_ticket_1294(gui):
	"""
	Boatbuilder crash with out of order finishing.
	"""

	settlement = gui.session.world.player.settlements[0]
	boatbuilder = settlement.buildings_by_id[BUILDINGS.BOAT_BUILDER][0]

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	# Select trade ships tab
	gui.trigger('tab_base/1')

	# Build huker
	gui.trigger('boatbuilder_showcase/ok_0')

	# Pause huker construction
	gui.trigger('UB_main_tab/toggle_active_active')

	# Select war ships tab
	gui.trigger('tab_base/2')

	# Build frigate
	gui.trigger('boatbuilder_showcase/ok_0')

	# Wait until production ends
	producer = boatbuilder.get_component(Producer)
	while len(producer.get_productions()) > 1:
		gui.run()

	# Unpause huker construction
	gui.trigger('UB_main_tab/toggle_active_inactive')

	while producer.get_productions():
		gui.run()


@gui_test(use_fixture='boatbuilder', timeout=120)
def test_ticket_1830(gui):
	"""
	Boatbuilder should not replace main production while it's paused.
	"""

	settlement = gui.session.world.player.settlements[0]
	boatbuilder = settlement.buildings_by_id[BUILDINGS.BOAT_BUILDER][0]
	producer = boatbuilder.get_component(Producer)

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	# Select trade ships tab
	gui.trigger('tab_base/1')

	# Build huker
	gui.trigger('boatbuilder_showcase/ok_0')

	# Pause huker construction
	gui.trigger('UB_main_tab/toggle_active_active')

	# Select war ships tab
	gui.trigger('tab_base/2')

	# Build frigate
	gui.trigger('boatbuilder_showcase/ok_0')

	# Check if Main-Production is still just Huker and is paused.
	assert len(producer.get_productions()) == 1
	assert producer.get_productions()[0].get_produced_units()[UNITS.HUKER_SHIP] == 1
	assert producer.get_productions()[0]._state == PRODUCTION.STATES.paused

	# One entry (Frigate) in queue
	assert len(producer.production_queue) == 1


@gui_test(use_fixture='boatbuilder', timeout=60)
def test_remove_from_queue(gui):
	"""
	Boatbuilder crashes when canceling a ship in the queue.
	"""

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	# Select trade ships tab
	gui.trigger('tab_base/1')

	# Build huker
	gui.trigger('boatbuilder_showcase/ok_0')

	# Select war ships tab
	gui.trigger('tab_base/2')

	# Build frigate
	gui.trigger('boatbuilder_showcase/ok_0')

	# Cancel queue -> crash
	gui.trigger('UB_main_tab/queue_elem_0')


@gui_test(use_fixture='boatbuilder', timeout=60)
def test_cancel_ticket_1424(gui):
	"""
	Boatbuilder crashes when canceling a ship build.
	"""

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	# Select trade ships tab
	gui.trigger('tab_base/1')

	# Build huker
	gui.trigger('boatbuilder_showcase/ok_0')

	# Select war ships tab
	gui.trigger('tab_base/2')

	# Build frigate
	gui.trigger('boatbuilder_showcase/ok_0')

	gui.run()

	# Cancel build completely -> crash
	gui.trigger('UB_main_tab/UB_cancel_button')


@gui_test(use_fixture='boatbuilder', timeout=60)
def test_save_load_ticket_1421(gui):
	"""
	Boatbuilder crashes when saving/loading while a ship is being produced.
	"""

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	# Select trade ships tab
	gui.trigger('tab_base/1')

	# Build huker
	gui.trigger('boatbuilder_showcase/ok_0')

	# Select war ships tab
	gui.trigger('tab_base/2')

	# Build frigate
	gui.trigger('boatbuilder_showcase/ok_0')

	# Save and reload game
	saveload(gui)


@gui_test(use_fixture='boatbuilder', timeout=120)
def test_ticket_1513(gui):
	"""
	Boat builder costs don't go back to normal after cancelling a ship.
	"""

	settlement = gui.session.world.player.settlements[0]
	boatbuilder = settlement.buildings_by_id[BUILDINGS.BOAT_BUILDER][0]

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	def running_costs():
		c = gui.find(name='UB_main_tab')
		return c.findChild(name='running_costs').text

	# Check (inactive) running costs
	assert running_costs() == '10', "Expected 10, got {}".format(running_costs())

	# Select trade ships tab
	gui.trigger('tab_base/1')

	# Build huker
	gui.trigger('boatbuilder_showcase/ok_0')

	# Wait until production starts
	producer = boatbuilder.get_component(Producer)
	while producer._get_current_state() != PRODUCTION.STATES.producing:
		gui.run()

	# Check (active) running costs
	assert running_costs() == '25', "Expected 25, got {}".format(running_costs())

	gui.run()

	# Cancel build
	gui.trigger('UB_main_tab/UB_cancel_button')

	# Check (inactive) running costs
	assert running_costs() == '10', "Expected 10, got {}".format(running_costs())


@gui_test(use_fixture='boatbuilder', timeout=120)
def test_ticket_1514(gui):
	"""
	Cancelling a ship doesn't update the ship builder's tab.
	"""

	settlement = gui.session.world.player.settlements[0]
	boatbuilder = settlement.buildings_by_id[BUILDINGS.BOAT_BUILDER][0]

	# Select boat builder
	gui.cursor_click(64, 10, 'left')

	# nothing being built, no cancel button visible
	assert not gui.find('UB_cancel_button')

	# Select trade ships tab
	gui.trigger('tab_base/1')

	# Build huker
	gui.trigger('boatbuilder_showcase/ok_0')

	assert gui.find('UB_cancel_button').isVisible()

	# Wait until production starts
	producer = boatbuilder.get_component(Producer)
	while producer._get_current_state() != PRODUCTION.STATES.producing:
		gui.run()

	gui.run()

	# Cancel build
	gui.trigger('UB_main_tab/UB_cancel_button')

	# The tab should have changed, no cancel button visible
	assert not gui.find('UB_cancel_button')
