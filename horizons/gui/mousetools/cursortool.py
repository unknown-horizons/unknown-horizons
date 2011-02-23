# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from fife import fife
import horizons.main

from horizons.util import Point
from horizons.util.living import LivingObject

class CursorTool(fife.IMouseListener, LivingObject):
	"""Basic tool for cursors."""
	def __init__(self, session):
		super(CursorTool, self).__init__()
		self.session = session
		horizons.main.fife.eventmanager.addMouseListener(self)

	def end(self):
		horizons.main.fife.eventmanager.removeMouseListener(self)
		super(CursorTool, self).end()

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

	def _get_world_location_from_event(self, evt):
		"""Returns the coordinates of an event at the map.
		@return Point with int coordinates"""
		screenpoint = fife.ScreenPoint(evt.getX(), evt.getY())
		mapcoord = self.session.view.cam.toMapCoordinates(screenpoint, False)
		# undocumented legacy formula to correct coords, probably
		return Point(int(round(math.floor(mapcoord.x + mapcoord.x) / 2.0 + 0.25)), \
		             int(round(math.floor(mapcoord.y + mapcoord.y) / 2.0 + 0.25)))

