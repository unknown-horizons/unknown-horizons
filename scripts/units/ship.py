# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify 
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
from unit import Unit

_STATE_NONE, _STATE_IDLE, _STATE_MOVE = xrange(3)

class Ship(Unit):
    """Class representing a ship"""

    def __init__(self, model, unit_name, layer, uniqInMap=True):
        """@var model: fife.Model: engine model beeing used.
        @var unit_name: str containing the units name.
        @var layer: fife.Layer on which the unit is present.
        @var uniqInMap: bool if the unit is unique.
        """
        Unit.__init__(self, model, unit_name, layer, uniqInMap)
        self.state = _STATE_NONE
        self.idlecounter = 1


    def onInstanceActionFinished(self, instance, action):
        self.idle()
        if action.Id() != 'idle':
            self.idlecounter = 1
        else:
            self.idlecounter += 1
	
    def start(self):
        self.idle()
	
    def idle(self):
        self.state = _STATE_IDLE
        self.unit.act('move', self.unit.getFacingLocation())
		
    def move(self, location):
        """Moves the ship to a certain location
        @var location: fife.Location to which the unit should move"""
        self.state = _STATE_MOVE
        self.unit.move('move', location, 2)

