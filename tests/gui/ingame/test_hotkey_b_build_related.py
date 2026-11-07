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

"""
Tests for hotkey 'b' opening build related menu (Issue #1569)
"""

from horizons.constants import BUILDINGS
from tests.gui import gui_test
from tests.gui.helper import found_settlement


@gui_test(use_fixture='plain', timeout=120)
def test_hotkey_b_opens_build_related_menu_for_lumberjack(gui):
    """
    Test that pressing 'b' hotkey opens build related menu when a lumberjack is selected.
    """
    # Found a settlement
    found_settlement(gui, (59, 1), (56, 3))

    # Build lumberjack
    gui.trigger('mainhud/build')
    gui.trigger('tab/button_03')  # Lumberjack button
    gui.cursor_click(52, 7, 'left')

    # Select lumberjack
    gui.cursor_click(52, 7, 'left')
    gui.run()  # Ensure selection is processed

    # Press 'b' key - should open build related menu (not general build menu)
    gui.press_key(gui.Key.B)

    # Verify build related tab is open (not general build menu)
    build_related_tab = gui.find(name='overview_buildrelated')
    assert build_related_tab is not None, "Build related tab should be open when lumberjack is selected and 'b' is pressed"

    # Verify general build menu is NOT open
    build_menu = gui.find(name='build_menu_tab_widget')
    assert build_menu is None, "General build menu should not be open when build related menu is available"


@gui_test(use_fixture='plain', timeout=120)
def test_hotkey_b_falls_back_to_general_build_menu_for_warehouse(gui):
    """
    Test that pressing 'b' hotkey falls back to general build menu when a warehouse is selected.
    """
    # Found a settlement
    found_settlement(gui, (59, 1), (56, 3))

    # Select warehouse (warehouse doesn't have build related buildings)
    gui.cursor_click(56, 3, 'left')
    gui.run()  # Ensure selection is processed

    # Press 'b' key - should open general build menu
    gui.press_key(gui.Key.B)

    # Verify general build menu is open. The menu's pychan widget is named
    # 'tab_base'; 'build_menu_tab_widget' is the name of the TabWidget wrapper.
    menu = gui.session.ingame_gui.get_cur_menu()
    assert getattr(menu, 'name', None) == 'build_menu_tab_widget', \
        "General build menu should be open when warehouse is selected and 'b' is pressed"

    # Verify build related tab is NOT open
    build_related_tab = gui.find(name='overview_buildrelated')
    assert build_related_tab is None, "Build related tab should not be open for warehouse"


@gui_test(use_fixture='plain', timeout=120)
def test_hotkey_b_falls_back_to_general_build_menu_for_multiple_selection(gui):
    """
    Test that pressing 'b' hotkey falls back to general build menu when multiple buildings are selected.
    """
    # Found a settlement
    found_settlement(gui, (59, 1), (56, 3))

    # Build lumberjack
    gui.trigger('mainhud/build')
    gui.trigger('tab/button_03')
    gui.cursor_click(52, 7, 'left')

    # Select both warehouse and lumberjack (multi-select)
    gui.cursor_drag((54, 2), (58, 8), 'left')
    gui.run()  # Ensure selection is processed

    # Press 'b' key - should open general build menu (or multi-select tab)
    gui.press_key(gui.Key.B)

    # Verify general build menu or multi-select tab is shown
    # (not the build related tab which requires single selection)
    build_related_tab = gui.find(name='overview_buildrelated')
    assert build_related_tab is None, "Build related tab should not be open for multi-selection"


@gui_test(use_fixture='plain', timeout=120)
def test_hotkey_b_auto_selects_single_related_building(gui):
    """
    Test that pressing 'b' on lumberjack auto-selects tree (single related building).
    The cursor should switch to building mode for tree.
    """
    # Found a settlement
    found_settlement(gui, (59, 1), (56, 3))

    # Build lumberjack
    gui.trigger('mainhud/build')
    gui.trigger('tab/button_03')
    gui.cursor_click(52, 7, 'left')

    # Select lumberjack
    gui.cursor_click(52, 7, 'left')
    gui.run()  # Ensure selection is processed

    # Press 'b' key - should open build related menu and auto-select tree
    gui.press_key(gui.Key.B)

    # Verify build related tab is open before the scheduled auto-select runs.
    build_related_tab = gui.find(name='overview_buildrelated')
    assert build_related_tab is not None, "Build related tab should be open"

    # The auto-select is scheduled on the next game tick. It closes the
    # build-related tab, so wait for the cursor to switch to building mode.
    from horizons.gui.mousetools.buildingtool import BuildingTool
    for _ in range(60):
        if isinstance(gui.cursor, BuildingTool):
            break
        gui.run()

    cursor = gui.cursor
    assert isinstance(cursor, BuildingTool), "Cursor should be in building mode after auto-select"
    assert cursor._class.id == BUILDINGS.TREE, "Cursor should be set to build tree"
