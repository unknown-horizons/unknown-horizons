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

from fife import fife

from horizons.command.unit import Act
from horizons.util import WorldObject
from selectiontool import SelectionTool
from horizons.constants import LAYERS

class AttackingTool(SelectionTool):
	#NOTE bug with selecting other units (tab not shown)
	#also keylisteners don't work
	"""
		This will be used when attacking units are selected
		it will have to respond on right click and change cursor image when hovering enemy units
	"""
	def __init__(self, session):
		super(AttackingTool, self).__init__(session)
		print 'entered attack mode'

	def mousePressed(self, evt):
		#NOTE for testing, catches only one right click event, then reverts to selection tool
		if (evt.getButton() == fife.MouseEvent.RIGHT):
			target_mapcoord = self.session.view.cam.toMapCoordinates(\
				fife.ScreenPoint(evt.getX(), evt.getY()), False)
			for i in self.session.selected_instances:
				#TODO attack command
				#dummy attack if possible
				try:
					i.attack(self._get_world_location_from_event(evt))
					print 'attacked from', i
				except AttributeError:
					pass
			evt.consume()
		else:
			super(AttackingTool, self).mousePressed(evt)
		self.session.cursor = SelectionTool(self.session)
		print 'exit attack mode'
