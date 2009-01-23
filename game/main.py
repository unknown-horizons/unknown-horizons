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

"""This is the main game file, it used to store some global information and to handle
   the main menu, as well as to initialize new gamesessions. game.main provides some globals
   that can be used throughout the code just by importing 'game.main'. These are the
   globals:
   * db - the game.dbreader instance, used to retrieve data from the database.
   * settings - game.settings instance.
   * fife - if a game is running. game.fife provides the running engine instance.
   * gui - provides the currently active gui (only non ingame menus)
   * session - game.session instance - check game/session.py for more information
   * connection - multiplayer game connection (not used yet)
   * ext_scheduler - game.extscheduler instance, used for non ingame timed events.
   * savegamemanager - game.savegamemanager instance.

   TUTORIAL:
   Continue to game.session for further ingame digging.
   """

import re
import time
import os
import os.path
import glob
import shutil
import random
import game.engine

from game.menus import Menus
from game.dbreader import DbReader
from game.engine import Fife
from game.settings import Settings
from game.session import Session
from game.gui.mainlistener import MainListener
from extscheduler import ExtScheduler
from game.savegamemanager import SavegameManager, InvalidSavegamenameException

def start():
	"""Starts the game.
	"""
	global db, settings, fife, gui, session, connection, ext_scheduler, savegamemanager
	#init db
	db = DbReader(':memory:')
	db("attach ? AS data", 'content/openanno.sqlite')

	#init settings
	settings = Settings()
	settings.addCategorys('sound')
	settings.sound.setDefaults(enabled = True)
	settings.sound.setDefaults(volume_music = 1.0)
	settings.sound.setDefaults(volume_effects = 1.0)
	settings.addCategorys('network')
	settings.network.setDefaults(port = 62666, url_servers = 'http://master.openanno.org/servers', url_master = 'master.openanno.org', favorites = [])
	settings.addCategorys('savegame')
	settings.savegame.setDefaults(savedquicksaves = 10, autosaveinterval = 10, savedautosaves = 10)

	if settings.client_id is None:
		settings.client_id = "".join("-" if c in (8,13,18,23) else random.choice("0123456789abcdef") for c in xrange(0,36))

	savegamemanager = SavegameManager()

	fife = Fife()
	ext_scheduler = ExtScheduler(fife.pump)

	fife.init()

	mainlistener = MainListener()
	connection = None
	session = None
	gui = Menus()

	gui.show_main()

	fife.run()

def quit():
	"""Quits the game"""
	global fife
	fife.cursor.set(game.engine.fife.CURSOR_NATIVE) #hack to get system cursor back
	fife.quit()


def start_singleplayer(map_file):
	"""Starts a singleplayer game"""
	global gui, session
	gui.show()

	fife.cursor.set(game.engine.fife.CURSOR_NONE)

	fife.engine.pump()

	fife.cursor.set(game.engine.fife.CURSOR_IMAGE, fife.default_cursor_image)

	gui.hide()

	session = Session()
	session.init_session()
	session.load(map_file, 'Arthur', Color()) # temp fix to display gold


def startMulti():
	"""Starts a multiplayer game server (dummy)

	This also starts the game for the game master
	"""
	pass

def saveGame():
	# Saving is disabled for now
	#showDialog(fife.pychan.loadXML('content/gui/save_disabled.xml'), {'okButton' : True}, onPressEscape = True)
	#return

	global session, savegamemanager

	savegame_files, savegame_display = savegamemanager.get_regular_saves()

	save_dlg = fife.pychan.loadXML('content/gui/ingame_save.xml')

	save_dlg.distributeInitialData({'savegamelist' : savegame_display})

	def tmp_selected_changed():
		"""Fills in the name of the savegame in the textbox when selected in the list"""
		save_dlg.distributeData({'savegamefile' : savegame_display[save_dlg.collectData('savegamelist')]})

	def tmp_delete_savegame():
		if delete_savegame(save_dlg, savegame_files):
			save_dlg.hide()
			saveGame()

	save_dlg.findChild(name='savegamelist').capture(tmp_selected_changed)
	if not showDialog(save_dlg, {'okButton' : True, 'cancelButton' : False},
										onPressEscape = False,
										event_map={'deleteButton' : tmp_delete_savegame}):
		return

	savegamename = save_dlg.collectData('savegamefile')

	try:
		savegamefile = savegamemanager.create_filename(savegamename)
	except InvalidSavegamenameException:
		return

	if os.path.exists(savegamefile):
		if not showPopup("Confirmation for overwriting",
										 "A savegame with the name \"%s\" already exists. Should i overwrite it?"%savegamename,
										 show_cancel_button = True):
			saveGame()
			return

	try:
		session.save(savegamefile)
	except IOError: # invalid filename
		showPopup("Invalid filename", "You entered an invalid filename.")
		save_dlg.hide()
		saveGame()

def loadGame(savegame = None):
	# Loading is disabled for now
	#showDialog(fife.pychan.loadXML('content/gui/load_disabled.xml'), {'okButton' : True}, onPressEscape = True)
	#return
	global session, gui, fife, savegamemanager

	if savegame is None:
		map_files, map_file_display = savegamemanager.get_saves()

		if len(map_files) == 0:
			gui.show_popup("No saved games", "There are no saved games to load")
			return

		load_dlg = fife.pychan.loadXML('content/gui/ingame_load.xml')

		load_dlg.distributeInitialData({'savegamelist' : map_file_display})

		def tmp_delete_savegame():
			if delete_savegame(load_dlg, map_files):
				load_dlg.hide()
				loadGame()

		load_dlg.findChild(name="savegamelist").capture(create_show_savegame_details(load_dlg, map_files, 'savegamelist'))
		if not showDialog(load_dlg, {'okButton' : True, 'cancelButton' : False},
											onPressEscape = False,
											event_map={'deleteButton' : tmp_delete_savegame}):
			return

		selected_savegame = load_dlg.collectData('savegamelist')
		if selected_savegame == -1:
			return
		savegamefile = map_files[ selected_savegame ]
	else:
		savegamefile = savegame

	assert(os.path.exists(savegamefile))

	if session is not None:
		session = None

	if gui is not None:
		gui.hide()
	gui = fife.pychan.loadXML('content/gui/loadingscreen.xml')
	gui.x += int((settings.fife.screen.width - gui.width) / 2)
	gui.y += int((settings.fife.screen.height - gui.height) / 2)
	gui.show()
	fife.engine.pump()

	session = Session()
	session.load(savegamefile)
	returnGame()


