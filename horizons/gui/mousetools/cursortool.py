# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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
import logging

from fife import fife
import horizons.globals

from horizons.util.shapes import Point


# round half towards plus infinity
# http://en.wikipedia.org/wiki/Rounding#Round_half_up
roundhalfplus = lambda x: int(round(math.floor(x + x) / 2.0 + 0.25))


class CursorTool(fife.IMouseListener):
	"""Basic tool for cursors."""
	log = logging.getLogger("gui.mousetools")

	def __init__(self, session):
		super(CursorTool, self).__init__()
		assert isinstance(session, horizons.session.Session)
		self.session = session
		self.enable()

	def enable(self):
		"""Call this to get events."""
		horizons.globals.fife.eventmanager.addMouseListener(self)

	def disable(self):
		"""Call this to not get events."""
		horizons.globals.fife.eventmanager.removeMouseListener(self)

	def remove(self):
		self.disable()

	def mousePressed(self, evt):
		pass
	def mouseReleased(self, evt):
		pass
	def mouseEntered(self, evt):
		pass
	def mouseExited(self, evt):
		pass
	def mouseClicked(self, evt):
		pass
	def mouseWheelMovedUp(self, evt):
		pass
	def mouseWheelMovedDown(self, evt):
		pass
	def mouseMoved(self, evt):
		pass
	def mouseDragged(self, evt):
		pass

	def _round_map_coords(self, map_x, map_y):
		"""Returns the coordinates of an event at the map.

		Why roundhalfplus?

		        a      b     a-b   round(a)-round(b)  roundplus(a)-roundplus(b)

		       1.50   0.50   1.00       1.00               1.0
		       0.50  -0.49   0.99       1.00               1.0
		      -0.49  -1.49   1.00       1.00               1.0
		Error: 0.50  -0.50   1.00       2.00               1.0

		This error would result in fields at position 0 to be smaller than the others,
		because both sides (-0.5 and 0.5) would be wrongly assigned to the other fields.

		@return Point with int coordinates"""
		return Point(roundhalfplus(map_x), roundhalfplus(map_y))

	def get_world_location(self, evt):
		screenpoint = self._get_screenpoint(evt)
		mapcoords = self.session.view.cam.toMapCoordinates(screenpoint, False)
		return self._round_map_coords(mapcoords.x, mapcoords.y)

	def get_exact_world_location(self, evt):
		"""Returns the coordinates of an event at the map.
		@return FifePoint with float coordinates or something with getX/getY"""
		screenpoint = self._get_screenpoint(evt)
		return self.session.view.cam.toMapCoordinates(screenpoint, False)

	def _get_screenpoint(self, arg):
		"""Python lacks polymorphism."""
		if isinstance(arg, fife.ScreenPoint):
			return arg
		else:
			return fife.ScreenPoint(arg.getX(), arg.getY())

	def end(self):
		self.session = None
		self.helptext = None
