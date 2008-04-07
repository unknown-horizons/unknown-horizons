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
        self.db = DbReader(':memory:')
        self.db.query("attach ? AS core", ('./core.sqlite'))
        class DefaultSettings():
            FullScreen          = 0 #
            ScreenWidth         = 1024 #
            ScreenHeight        = 768 #
            BitsPerPixel        = 0 #
            RenderBackend       = "OpenGL" #
            InitialVolume       = 5.0 #
            PlaySounds          = 1 #
            SDLRemoveFakeAlpha  = 1
            Font                = 'content/gfx/fonts/samanata.ttf'
            FontSize            = 12
            FontGlyphs          = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,!?-+/():;%&`'*#=[]\""
            LogModules          = ['controller'] #'all' for everything
            PychanDebug         = False
            LogToPrompt         = 1
            LogToFile           = 1
            UsePsyco            = False
            ImageChunkSize      = 256
        self.settings = DefaultSettings()
        self.db.query("attach ? AS config", ('./config.sqlite'))
        for (name, value) in self.db.query("select name, value from config.config where ((name = 'screen_full' and value in ('0', '1')) or (name = 'screen_width' and value regexp '^[0-9]+$') or (name = 'screen_height' and value regexp '^[0-9]+$') or (name = 'screen_bpp' and value in ('16', '24', '32')) or (name = 'screen_renderer' and value in ('SDL', 'OpenGL')) or (name = 'sound_volume' and value regexp '^[0-9]+([.][0-9]+)?$'))").rows:
            if name == 'screen_full':
                self.settings.FullScreen = int(value)
            if name == 'screen_width':
                self.settings.ScreenWidth = int(value)
            if name == 'screen_height':
                self.settings.ScreenHeight = int(value)
            if name == 'screen_bpp':
                self.settings.BitsPerPixel = int(value)
            if name == 'screen_renderer':
                self.settings.RenderBackend = str(value)
            if name == 'sound_volume':
                self.settings.InitialVolume = float(value)
        
        super(OpenAnno, self).__init__() 
        
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

    def loadSettings(self):
        """
        Load the settings from a python file and load them into the engine.
        Called in the ApplicationBase constructor.
        """
        engineSetting = self.engine.getSettings()
        engineSetting.setDefaultFontGlyphs(self.settings.FontGlyphs)
        engineSetting.setDefaultFontPath(self.settings.Font)
        engineSetting.setDefaultFontSize(self.settings.FontSize)
        engineSetting.setBitsPerPixel(self.settings.BitsPerPixel)
        engineSetting.setFullScreen(self.settings.FullScreen)
        engineSetting.setInitialVolume(self.settings.InitialVolume)
        engineSetting.setRenderBackend(self.settings.RenderBackend)
        engineSetting.setSDLRemoveFakeAlpha(self.settings.SDLRemoveFakeAlpha)
        engineSetting.setScreenWidth(self.settings.ScreenWidth)
        engineSetting.setScreenHeight(self.settings.ScreenHeight)
        try:
            engineSetting.setImageChunkingSize(self.settings.ImageChunkSize)
        except:
            pass

    def showCredits(self):
        pychan.loadXML('content/gui/credits.xml').execute({ 'okButton' : True })

    def showSettings(self):
        resolutions = ["640x480", "800x600", "1024x768", "1440x900"];
        try:
            resolutions.index(str(self.engine.getSettings().getScreenWidth()) + 'x' + str(self.engine.getSettings().getScreenHeight()))
        except:
            resolutions.append(str(self.engine.getSettings().getScreenWidth()) + 'x' + str(self.engine.getSettings().getScreenHeight()))
        dlg = pychan.loadXML('content/gui/settings.xml')
        dlg.distributeInitialData({
           'screen_resolution' : resolutions,
           'screen_renderer' : ["OpenGL", "SDL"],
           'screen_bpp' : ["Desktop", "16", "24", "32"]
        })
        dlg.distributeData({
           'screen_resolution' : resolutions.index(str(self.engine.getSettings().getScreenWidth()) + 'x' + str(self.engine.getSettings().getScreenHeight())),
           'screen_renderer' : 0 if self.settings.RenderBackend == 'OpenGL' else 1,
           'screen_bpp' : int(self.settings.BitsPerPixel / 10), # 0:0 16:1 24:2 32:3 :)
           'screen_fullscreen' : self.settings.FullScreen == 1
        })
        if(not dlg.execute({ 'okButton' : True, 'cancelButton' : False })):
            return;
        screen_resolution, screen_renderer, screen_bpp, screen_fullscreen = dlg.collectData('screen_resolution', 'screen_renderer', 'screen_bpp', 'screen_fullscreen')
        if screen_fullscreen != self.settings.FullScreen == 1:
            self.settings.FullScreen = (1 if screen_fullscreen else 0)
            self.engine.getSettings().setFullScreen(self.settings.FullScreen)
        if screen_bpp != int(self.settings.BitsPerPixel / 10):
            self.settings.BitsPerPixel = (0 if screen_bpp == 0 else ((screen_bpp + 1) * 8))
            self.engine.getSettings().setBitsPerPixel(self.settings.BitsPerPixel)

    def showQuit(self):
        if self.game is None:
            if(pychan.loadXML('content/gui/quitgame.xml').execute({ 'okButton' : True, 'cancelButton' : False })):
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
