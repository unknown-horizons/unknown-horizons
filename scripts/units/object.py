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
import common, fife

class Object(fife.InstanceActionListener):
    def __init__(self, model, object_id, layer, game, uniqInMap=True):
        """
        @var model: fife.Model: engine model beeing used.
        @var unit_id: str containing the objects id.
        @var layer: fife.Layer on which the object is present.
        @var game: Main Game class instance
        @var uniqInMap: bool if the object is unique.
        """
        fife.InstanceActionListener.__init__(self)
        self.model = model
        self.object_id = object_id
        self.layer = layer
        self.type = None
        self.game = game
        self.health = 100
        if uniqInMap:
            self.object = layer.getInstances('id', object_id)[0]
            self.object.addActionListener(self)

    def onInstanceActionFinished(self, instance, action):
        raise ProgrammingError('No OnActionFinished defined for Unit.')

    def start(self):
        raise ProgrammingError('No start defined for Unit.')
