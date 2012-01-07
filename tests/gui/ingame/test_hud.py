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

from tests.gui import gui_test, TestFinished


@gui_test(use_dev_map=True)
def test_hud(gui):
	"""
	Example test generated with output from --gui-log.
	"""
	yield # test needs to be a generator for now

	c = gui.find(name='mainhud')
	gui.trigger(c, 'zoomOut/action/default')

	c = gui.find(name='mainhud')
	gui.trigger(c, 'zoomIn/action/default')

	c = gui.find(name='mainhud')
	gui.trigger(c, 'rotateRight/action/default')

	c = gui.find(name='mainhud')
	gui.trigger(c, 'rotateLeft/action/default')

	c = gui.find(name='mainhud')
	gui.trigger(c, 'logbook/action/default')

	c = gui.find(name='captains_log')
	gui.trigger(c, 'okButton/action/default')

	c = gui.find(name='mainhud')
	gui.trigger(c, 'build/action/default')

	c = gui.find(name='mainhud')
	gui.trigger(c, 'diplomacyButton/action/default')

	raise TestFinished
