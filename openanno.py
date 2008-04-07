#!/usr/bin/env python

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

import sys
import os
import re

import settings

def _jp(path):
    return os.path.sep.join(path.split('/'))

_paths = (settings.path + 'engine/swigwrappers/python', settings.path + 'engine/extensions')

for p in _paths:
    if p not in sys.path:
        sys.path.append(_jp(p)) 

# Do all the necessary imports
try:
    import fife
    import fifelog
    import pychan

except ImportError,e:
    print 'FIFE was not found or failed to load'
    print 'Reason: ' + e.message
    print "Please edit settings.py and change 'path' to point to your FIFE checkout"
    exit()

import basicapplication
from scripts.keylistener import KeyListener
from scripts.game import Game
from scripts.dbreader import DbReader


class OpenAnno(basicapplication.ApplicationBase):
    """OpenAnno class, main game class. Creates the base."""
    def __init__(self):
        super(OpenAnno, self).__init__() 
        
        self.db = DbReader(':memory:')
        self.db.query("attach ? AS config", ('./config.sqlite'))
        self.db.query("attach ? AS core", ('./core.sqlite'))
        self.db.query("begin transaction")
        print self.db.query("select * from config.config;").rows
        pychan.init(self.engine,debug=False)
        pychan.setupModalExecution(self.mainLoop,self.breakFromMainLoop)
        
        self.mainmenu = pychan.loadXML('content/gui/mainmenu.xml')
        self.gamemenu = pychan.loadXML('content/gui/gamemenu.xml')
        
        eventMap = {
            'startGame' : self.start_game,
            'settingsLink' : self.showSettings,
            'creditsLink'  : self.showCredits,
            'closeButton'  : self.showQuit,
        }
        self.mainmenu.mapEvents(eventMap)
        self.gamemenu.mapEvents(eventMap)
        self.gui = self.mainmenu
        self.gui.show()
        self.game = None

    def showCredits(self):
        pychan.loadXML('content/gui/credits.xml').execute({ 'okButton' : True })

    def showSettings(self):
        pychan.loadXML('content/gui/settings.xml').execute({ 'okButton' : True })

    def showQuit(self):
        if self.game is None:
            if(pychan.loadXML('content/gui/quitgame.xml').execute({ 'okButton' : True, 'cancelButton' : False })):
                self.db.query("commit transaction")
                self.db.query("detach core")
                self.db.query("detach config")
                self.quit()
        else:
            if(pychan.loadXML('content/gui/quitsession.xml').execute({ 'okButton' : True, 'cancelButton' : False })):
                self.game = None
                self.gui.hide()
                self.gui = self.mainmenu
                self.gui.show()

    def start_game(self):
        self.gui.hide()
        self.gui = self.gamemenu
        if self.game is None:
            self.game = Game(self.engine, settings.MapFile)

    def createListener(self):
        self.listener = KeyListener(self.engine, self) 


# main methode, creates an OpenAnno instance
def main():
    app = OpenAnno() 
    app.run() 

if __name__ == '__main__':
    main() 
