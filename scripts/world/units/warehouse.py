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
from house import House

_STATE_NONE, _STATE_IDLE, _STATE_MOVE = xrange(3)

class Warehouse(House):
    """Class representing a Warehouse"""

    def __init__(self, model, object_name, layer, game, player, uniqInMap=True):
        """
        @var model: fife.Model: engine model beeing used.
        @var object_name: str containing the objects name used in the map.
        @var layer: fife.Layer on which the object is present.
        @var game: Game instance of the main.
        @var player: Player instance that built the bulding
        @var uniqInMap: bool if the object is unique.
        """
        House.__init__(self, model, object_name, layer, game, uniqInMap)
        self.state = _STATE_NONE
        self.type = 'building'
        self.size_x = 0
        self.size_y = 0
        self.res = 0
        self.player = player

    def onInstanceActionFinished(self, instance, action):
        self.idle()
    
    def start(self):
        self.idle()

    def idle(self):
        self.state = _STATE_IDLE

    def on_build(self):
        self.game.create_settlement(player)

