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
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

from horizons.constants import BUILDINGS
from tests.gui import gui_test
from tests.gui.helper import found_settlement


@gui_test(use_dev_map=True)
def test_tearing(gui):
	settlement = found_settlement(gui, (11, 1), (11, 6))
	world = gui.session.world

	def tree_ids():
		return {building.worldid for building in world.get_all_buildings()
		        if building.id == BUILDINGS.TREE}

	# Tear down some trees with the destroy tool.
	trees_before = tree_ids()
	gui.trigger('mainhud/destroy_tool')
	gui.cursor_drag((5, 7), (11, 16), 'left')
	trees_after_first_tear = tree_ids()
	assert len(trees_after_first_tear) < len(trees_before)

	# Build 4 residential tents.
	gui.trigger('mainhud/build')
	gui.trigger('tab/button_01')
	gui.cursor_drag((7, 9), (10, 12), 'left')
	assert len(settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]) == 4

	# Tear down an area that includes the tents, some trees and the warehouse.
	# The warehouse is not tearable, so it has to survive.
	warehouse = settlement.buildings_by_id[BUILDINGS.WAREHOUSE][0]
	gui.trigger('mainhud/destroy_tool')
	gui.cursor_drag((5, 15), (15, 3), 'left')

	assert not settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]
	assert settlement.buildings_by_id[BUILDINGS.WAREHOUSE] == [warehouse]


def _build_storage_tent(gui, x, y):
	"""Build a storage tent and return it.

	A storage tent is used because it is an EXPAND_RANGE building (so removing it
	can shrink the settlement range) and, unlike the warehouse, it is tearable.
	"""
	gui.trigger('tab/button_11')  # storage tent
	gui.cursor_click(x, y, 'left')
	gui.run(seconds=0.1)
	return next(b for b in gui.session.world.player.settlements[-1].buildings
	            if b.id == BUILDINGS.STORAGE)


def _build_residential_tents(gui, start, end):
	"""Build a row of residential tents and return them."""
	gui.trigger('tab/button_01')  # residential tents
	gui.cursor_drag(start, end, 'left')
	gui.run(seconds=0.1)
	return list(gui.session.world.player.settlements[-1].buildings_by_id[BUILDINGS.RESIDENTIAL])


def _tear_with_confirmation(gui, building, button):
	"""Tear down `building` with the destroy tool and answer the popup."""
	xs = [coord[0] for coord in building.position.tuple_iter()]
	ys = [coord[1] for coord in building.position.tuple_iter()]
	start = (min(xs), min(ys))
	end = (max(xs), max(ys))

	def answer_popup():
		# The popup is opened from mouseReleased, which runs after the handler
		# greenlet has already been scheduled, so wait until it is visible.
		for _ in range(1000):
			if gui.find('popup_window') is not None:
				break
			gui.run()
		else:
			raise AssertionError("confirmation popup did not appear")
		assert gui.find('popup_window/headline').text == 'Abandon buildings'
		gui.trigger('popup_window/' + button)

	with gui.handler(answer_popup):
		gui.trigger('mainhud/destroy_tool')
		gui.cursor_drag(start, end, 'left')


@gui_test(use_dev_map=True, timeout=60)
def test_tearing_confirmation_accept(gui):
	"""
	Test that tearing down a storage tent with outlying buildings shows confirmation
	and accepting it abandons the buildings.
	"""
	settlement = found_settlement(gui, (11, 1), (11, 6))

	# The storage tent extends the settlement range far enough to build tents
	# that the warehouse alone would not cover.
	gui.trigger('mainhud/build')
	storage_tent = _build_storage_tent(gui, 30, 6)
	tents = _build_residential_tents(gui, (38, 6), (40, 7))
	assert tents, "residential tents should have been built"

	_tear_with_confirmation(gui, storage_tent, 'okButton')

	assert gui.session.world.get_building(storage_tent.position.origin.to_tuple()) is None
	assert not settlement.buildings_by_id[BUILDINGS.STORAGE]
	assert not settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]


@gui_test(use_dev_map=True, timeout=60)
def test_tearing_confirmation_cancel(gui):
	"""
	Test that cancelling the confirmation preserves outlying buildings.
	"""
	settlement = found_settlement(gui, (11, 1), (11, 6))

	gui.trigger('mainhud/build')
	storage_tent = _build_storage_tent(gui, 30, 6)
	tents = _build_residential_tents(gui, (38, 6), (40, 7))
	assert tents, "residential tents should have been built"

	_tear_with_confirmation(gui, storage_tent, 'cancelButton')

	# The building that was torn down is gone, but the outlying tents survive.
	assert gui.session.world.get_building(storage_tent.position.origin.to_tuple()) is None
	assert not settlement.buildings_by_id[BUILDINGS.STORAGE]
	assert settlement.buildings_by_id[BUILDINGS.RESIDENTIAL] == tents


@gui_test(use_dev_map=True)
def test_pipette(gui):
	found_settlement(gui, (11, 1), (11, 6))

	# select mountain, can not be build
	gui.press_key(gui.Key.O)
	gui.cursor_click(6, 18, 'left')
	assert not gui.find('place_building')

	# build signal fire
	gui.trigger('mainhud/build')
	gui.trigger('tab/button_22')
	gui.cursor_click(7, 7, 'left')

	# activate pipette, select signal fire, place it next to the other
	gui.press_key(gui.Key.O)
	gui.cursor_click(7, 7, 'left')
	gui.cursor_click(6, 7, 'left')

	# select signal fire, check if it's actually there
	gui.cursor_click(6, 7, 'left')
	assert gui.find('overview_signalfire')