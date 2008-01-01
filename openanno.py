#!/usr/bin/env python

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

from openanno.gui import Gui
from openanno.world import World

MAPFILE = 'content/datasets/maps/openanno-test-map.xml'

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
	
	gui = Gui(engine)
	w = World(engine, gui)

	w.create_world(MAPFILE)
	w.adjust_views()

	if TDS.PlaySounds:
		w.create_background_music()
	w.run()