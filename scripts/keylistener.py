# ###################################################
# Copyright (C) 2008 The OpenAnno Team
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

import fife

class KeyListener(fife.IKeyListener):
    """KeyListener Class to process key presses"""

    def __init__(self, engine, main):
        """@var engine: Game engine"""
        super(KeyListener, self).__init__() 
        self.main = main
        engine.getEventManager().addKeyListener(self) 

    def keyPressed(self, evt):
        keyval = evt.getKey().getValue() 
        if keyval == fife.Key.ESCAPE:
            if self.main.gui.isVisible() and self.main.game is not None:
                self.main.gui.hide()
            elif self.main.gui.isVisible() and self.main.game is None:
                self.main.quit()
            elif not self.main.gui.isVisible():
                self.main.gui.show()
            evt.consume() 

    def keyReleased(self, evt):
        pass 


