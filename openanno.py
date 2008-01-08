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

import sys, os, re

def _jp(path):
	return os.path.sep.join(path.split('/'))

try:
	import fife, fifelog
except ImportError,e:
	print 'FIFE was not found or failed to load'
	print 'Reason: ' + e.message
	print 'Please edit start_oa.sh or start_oa.bat and change fife_dir to point to your FIFE checkout'
	exit()

import openanno_settings as TDS
import openanno.statemanager as StateManager

if __name__ == '__main__':
	engine = fife.Engine()
	log = fifelog.LogManager(engine, TDS.LogToPrompt, TDS.LogToFile)
	if TDS.LogModules:
		log.setVisibleModules(*TDS.LogModules)
	
	s = engine.getSettings()
	s.setDefaultFontGlyphs(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" +
			".,!?-+/:();%`'*#=[]")
	s.setDefaultFontPath('content/gfx/fonts/samanata.ttf')
	s.setDefaultFontSize(12)
	s.setBitsPerPixel(TDS.BitsPerPixel)
	s.setFullScreen(TDS.FullScreen)
	s.setInitialVolume(TDS.InitialVolume)
	s.setRenderBackend(TDS.RenderBackend)
	s.setSDLRemoveFakeAlpha(TDS.SDLRemoveFakeAlpha)
	s.setScreenWidth(TDS.ScreenWidth)
	s.setScreenHeight(TDS.ScreenHeight)
	engine.init()
	
	StateManager.init(engine)
	StateManager.get_instance().run()